#!/usr/bin/env python3
"""Build an isolated, schema-preserving image pilot and real-template browser preview."""
import copy
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from card_visuals import image_bytes
SOURCE = ROOT / 'GENKI II Vocab.apkg'
OUT = HERE / 'build'


def render(template, fields):
    for key, value in fields.items():
        for marker, keep in [('#', bool(value)), ('^', not value)]:
            template = re.sub(r'{{' + re.escape(marker + key) + r'}}(.*?){{/' + re.escape(key) + r'}}',
                              lambda m: m[1] if keep else '', template, flags=re.S)
    def field(match):
        name = match[1]
        if name.startswith('furigana:'):
            return re.sub(r'([^\s<>\[\]]+)\[([^\]]+)\]', r'<ruby>\1<rt>\2</rt></ruby>', fields[name[9:]])
        return fields[name]
    return re.sub(r'{{([^{}]+)}}', field, template)


def main():
    OUT.mkdir(exist_ok=True)
    entries = json.loads((ROOT / 'assets/card-visuals/manifest.json').read_text())
    assert len({(e['word'], e['reading']) for e in entries}) == len(entries)
    css = (ROOT / 'templates/card.css').read_text() + '\n' + (ROOT / 'templates/visuals.css').read_text()
    runtime = (ROOT / 'templates/runtime.js').read_text() + '\n' + (ROOT / 'templates/visuals.js').read_text()
    guard = (ROOT / 'templates/tap_guard.js').read_text()
    with tempfile.TemporaryDirectory() as temp, zipfile.ZipFile(SOURCE) as original:
        original.extract('collection.anki21', temp)
        db = Path(temp) / 'collection.anki21'
        con = sqlite3.connect(db)
        before = con.execute('select * from notes order by id').fetchall()
        available = {tuple(row[6].split('\x1f')[:2]) for row in before}
        entries = [e for e in entries if (e['word'], e['reading']) in available]
        cards = con.execute('select * from cards order by id').fetchall()
        models = json.loads(con.execute('select models from col').fetchone()[0])
        schema = {k: (m['flds'], [(t['name'], t['ord']) for t in m['tmpls']]) for k, m in models.items()}
        media = json.loads(original.read('media'))
        stroke = next(n for n in media.values() if n.startswith('_kanji_strokes_') and n.endswith('.js'))
        added = {}
        now = int(time.time())
        updated_ids = set()
        for entry in entries:
            image = image_bytes(ROOT / 'assets/card-visuals', entry)
            filename = 'vocab_visual_' + hashlib.sha256(image).hexdigest()[:16] + '.webp'
            entry['filename'] = filename
            index = next((k for k, v in media.items() if v == filename), str(max(map(int, media), default=-1) + 1))
            media[index] = filename
            added[index] = image
            matches = []
            for row in before:
                f = row[6].split('\x1f')
                if f[:2] == [entry['word'], entry['reading']]:
                    matches.append((row, f))
            assert matches, f"Expected an exact match: {entry['word']}"
            for row, fields in matches:
                fields[7] = re.sub(r'<figure class="vocab-visual">.*?</figure>', '', fields[7], flags=re.S)
                fields[7] = '<figure class="vocab-visual"><img src="' + filename + '" alt="' + html.escape(entry['alt'], quote=True) + '"></figure>' + fields[7]
                con.execute('update notes set flds=?, mod=?, usn=-1 where id=?', ('\x1f'.join(fields), max(now, row[3] + 1), row[0]))
                updated_ids.add(row[0])
        for model in models.values():
            model['css'] = css
            model['mod'] = max(now, model['mod'] + 1)
            model['usn'] = -1
            for template in model['tmpls']:
                stem = template['name'].lower()
                template['qfmt'] = (ROOT / f'templates/{stem}_front.html').read_text().replace('__VISUAL_FRONT__', (ROOT / 'templates/visual_front.js').read_text())
                template['afmt'] = (ROOT / f'templates/{stem}_back.html').read_text().replace('__RUNTIME__', runtime).replace('__TAP_GUARD__', guard).replace('_kanji_strokes.js', stroke)
                assert '<figure' not in template['qfmt'] and 'KanjiBreakdown' not in template['qfmt']
        con.execute('update col set models=?, mod=?', (json.dumps(models), now * 1000))
        con.commit()
        after = con.execute('select * from notes order by id').fetchall()
        assert len(before) == len(after)
        for old, new in zip(before, after):
            if old[0] not in updated_ids:
                assert old == new
            else:
                assert all(old[i] == new[i] for i in range(len(old)) if i not in (3, 4, 6))
                a, b = old[6].split('\x1f'), new[6].split('\x1f')
                assert all(a[i] == b[i] for i in range(len(a)) if i != 7)
                assert b[7].endswith(re.sub(r'<figure class="vocab-visual">.*?</figure>', '', a[7], flags=re.S))
        assert cards == con.execute('select * from cards order by id').fetchall()
        assert schema == {k: (m['flds'], [(t['name'], t['ord']) for t in m['tmpls']]) for k, m in models.items()}
        refs = set()
        for row in after:
            refs.update(re.findall(r'(?:src="|\[sound:)([^"\]]+)', row[6]))
        assert refs <= set(media.values()), refs - set(media.values())
        assert con.execute('pragma integrity_check').fetchone()[0] == 'ok'
        con.close()
        target = OUT / 'GENKI II Vocab - image pilot.apkg'
        staged = Path(temp) / 'pilot.apkg'
        with zipfile.ZipFile(staged, 'w', compression=zipfile.ZIP_DEFLATED) as package:
            for info in original.infolist():
                if info.filename not in ('collection.anki21', 'media') and info.filename not in added:
                    package.writestr(copy.copy(info), original.read(info.filename))
            package.write(db, 'collection.anki21')
            package.writestr('media', json.dumps(media))
            for index, data in added.items():
                package.writestr(index, data)
        with zipfile.ZipFile(staged) as check:
            assert check.testzip() is None
            assert all(index in check.namelist() for index in media)
            for info in original.infolist():
                if info.filename not in ('collection.anki21', 'media') and info.filename not in added:
                    assert check.read(info.filename) == original.read(info.filename)
            # Browser preview uses exactly the packaged templates, fields, CSS and media.
            assets = OUT / 'media'
            assets.mkdir(exist_ok=True)
            for index, filename in media.items():
                assert Path(filename).name == filename
                (assets / filename).write_bytes(check.read(index))
        target.write_bytes(staged.read_bytes())
        samples = []
        # Keep the interactive page small; the gallery and export retain every image.
        preview_words = ['運ぶ'] + [e['word'] for e in entries if e['word'] not in ('運ぶ', '落ち込む')]
        preview_words = list(dict.fromkeys(preview_words))[:40]
        for row in after:
            fields = row[6].split('\x1f')
            if fields[0] not in preview_words and fields[0] != '落ち込む':
                continue
            if fields[0] == '落ち込む':
                fields[7] = re.sub(r'<figure class="vocab-visual">.*?</figure>', '', fields[7], flags=re.S)
            model = models[str(row[2])]
            values = dict(zip([f['name'] for f in model['flds']], fields))
            for template in model['tmpls']:
                for side in ['qfmt', 'afmt']:
                    content = render(template[side], values)
                    content = re.sub(r'\[sound:([^\]]+)\]', r'<a href="#" onclick="event.preventDefault();this.nextElementSibling.play()">Play</a><audio src="\1"></audio>', content)
                    doc = '<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><base href="media/"><style>' + css + '</style><body>' + content + '</body></html>'
                    samples.append({'word': fields[0], 'type': template['name'], 'side': side, 'doc': doc})
        data = json.dumps(samples, ensure_ascii=False).replace('</', '<\\/')
        preview_entries = sorted((e for e in entries if e['word'] in preview_words), key=lambda e: e['word'] != '運ぶ')
        preview_images = {e['filename']: 'media/' + e['filename'] for e in preview_entries}
        page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Card image pilot</title>
<style>body{font:16px system-ui;background:#f3f1ec;color:#242824;margin:24px auto;max-width:900px;padding:0 16px}h1{font-size:25px}label,button{margin:6px;display:inline-block}select,button{font:inherit;padding:8px;max-width:100%}iframe{display:block;box-sizing:border-box;width:100%;max-width:642px;height:760px;border:1px solid #ccc;border-radius:16px;background:white;margin:20px auto}.night{background:#222;color:#eee}</style>
<h1>Images after the reveal</h1><a href="gallery.html">Compare all illustrations</a><p>__COUNT__ illustrated words and one unillustrated control. Compare both card directions, with or without the image. This preview uses the experimental deck templates. Audio and stroke animations are included.</p>
<label>Word <select id="word"></select></label><label>Direction <select id="direction"><option>Recognition</option><option>Production</option></select></label><button id="flip">Show answer</button><label><input id="images" type="checkbox" checked>Images</label><label><input id="night" type="checkbox">Night mode</label><iframe title="Anki card preview" id="card"></iframe>
<script>let cardObserver;function sizeCard(){const body=frame.contentDocument?.body;if(!body)return;frame.style.height=Math.ceil(body.offsetHeight+16)+'px';}function observeCard(){cardObserver?.disconnect();const body=frame.contentDocument?.body;if(!body)return;cardObserver=new ResizeObserver(sizeCard);cardObserver.observe(body);sizeCard();}const samples=__DATA__;const embeddedImages=__IMAGES__;const preloadImages=Object.keys(embeddedImages).map(name=>{const img=new Image();img.fetchPriority=name===Object.keys(embeddedImages)[0]?'high':'low';img.src=embeddedImages[name];return img;});let answer=false;const word=document.getElementById('word'),direction=document.getElementById('direction'),images=document.getElementById('images'),night=document.getElementById('night'),frame=document.getElementById('card'),flip=document.getElementById('flip');[...new Set(samples.map(s=>s.word))].forEach(w=>word.add(new Option(w,w)));word.value='運ぶ';function draw(){const s=samples.find(s=>s.word===word.value&&s.type===direction.value&&s.side===(answer?'afmt':'qfmt'));let doc=s.doc.replace(/src="([^"]+)"/g,(match,name)=>embeddedImages[name]?'src="'+name+'"':match);if(!images.checked)doc=doc.replace('</style>','.vocab-visual{display:none!important}</style>');if(night.checked)doc=doc.replace('<body>','<body class="nightMode night_mode">');if(frame.contentDocument&&frame.contentDocument.querySelector('.card')){const parsed=new DOMParser().parseFromString(doc,'text/html');const live=frame.contentDocument;live.head.innerHTML=parsed.head.innerHTML;live.body.className=parsed.body.className;live.body.replaceChildren(...Array.from(parsed.body.childNodes).map(n=>live.importNode(n,true)));live.querySelectorAll('script').forEach(old=>{const fresh=live.createElement('script');for(const attr of old.attributes)fresh.setAttribute(attr.name,attr.value);fresh.textContent=old.textContent;old.replaceWith(fresh);});}else{frame.srcdoc=doc;}flip.textContent=answer?'Show question':'Show answer';if(frame.contentDocument?.querySelector('.card'))observeCard();}flip.onclick=()=>{answer=!answer;draw();if(answer){const audio=frame.contentDocument?.querySelector('.word-audio-hidden audio');if(audio){audio.currentTime=0;audio.play().catch(error=>console.warn('Word audio playback failed:',error));}}};word.onchange=direction.onchange=()=>{answer=false;draw()};images.onchange=night.onchange=draw;frame.onload=observeCard;draw();</script></html>'''.replace('__COUNT__', str(len(preview_words))).replace('__DATA__', data).replace('__IMAGES__', json.dumps(preview_images))
        (OUT / 'preview.html').write_text(page)
        gallery_cards = []
        for entry in entries:
            gallery_cards.append('<article><h2>' + html.escape(entry['word']) + ' <small>' + html.escape(entry['reading']) + '</small></h2><div class="art"><img src="media/' + entry['filename'] + '" alt="' + html.escape(entry['alt'], quote=True) + '"></div><p>' + html.escape(entry['reason']) + '</p></article>')
        gallery = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Image study — illustrated vocabulary</title><style>body{font:16px system-ui;margin:24px auto;padding:0 20px;max-width:1100px;background:#f3f1ec;color:#242824}header{margin-bottom:24px}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}article{border:1px solid #bbb;border-radius:16px;overflow:hidden;background:white}h2,p{padding:0 16px}h2{font-size:22px}small{font-size:14px;font-weight:400}p{font-size:14px;line-height:1.5}.art{background:white}.art img{display:block;width:100%;aspect-ratio:3/1;object-fit:contain;box-sizing:border-box;padding:4% 6%}body.dark .art{background:#202020}@media(max-width:600px){main{grid-template-columns:1fr}}</style><header><h1>Illustration examples</h1><p>Shared catalog illustrations and reused examples. These are memory cues for the answer side; the notes below call out ambiguity.</p><a href="preview.html">Interactive card preview</a> <label><input type="checkbox" onchange="document.body.classList.toggle(\'dark\',this.checked)"> Dark image background</label></header><main>' + ''.join(gallery_cards) + '</main></html>'
        (OUT / 'gallery.html').write_text(gallery)

        report = {'source': SOURCE.name, 'notes': len(after), 'cards': len(cards), 'illustrated_notes': len(updated_ids), 'added_image_bytes': sum(map(len, added.values())), 'verified': ['note IDs/GUIDs unchanged', 'card rows unchanged', 'field schema unchanged', 'only selected breakdown fields changed', 'all original media and stub bytes unchanged', 'all note media references resolve', 'SQLite integrity and ZIP CRC pass', 'fronts have no images']}
        (OUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        print(target)
        print(OUT / 'preview.html')


if __name__ == '__main__':
    main()
