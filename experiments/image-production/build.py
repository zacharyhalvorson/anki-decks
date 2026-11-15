"""Build a local-only image production preview; never writes deck packages."""
import json, re, sqlite3, sys, tempfile, zipfile, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from card_visuals import image_bytes
out = HERE / 'media'
out.mkdir(exist_ok=True)
manifest = json.loads((ROOT / 'assets/card-visuals/manifest.json').read_text())
words = ['階段', '財布', '傘', '猫', '時計', '自転車']
spec = importlib.util.spec_from_file_location('preview_builder', ROOT / 'experiments/card-visuals/build.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
css = (ROOT / 'templates/card.css').read_text() + '\n' + (ROOT / 'templates/visuals.css').read_text()
runtime = (ROOT / 'templates/runtime.js').read_text()
(out / '_kanji_strokes.js').write_bytes((ROOT / 'assets/_kanji_strokes.js').read_bytes())
fields = ['Word', 'Reading', 'Meaning', 'PartOfSpeech', 'ExampleJA', 'FuriganaExample', 'ExampleEN', 'KanjiBreakdown', 'WordAudio', 'ExampleAudio']
samples = {}
for deck in ['GENKI II Vocab.apkg', 'JLPT N5.apkg', 'JLPT N4.apkg']:
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(ROOT / 'decks' / deck) as z:
        z.extract('collection.anki21', tmp)
        media = {v:k for k,v in json.loads(z.read('media')).items()}
        with sqlite3.connect(str(Path(tmp) / 'collection.anki21')) as db:
            for (raw,) in db.execute('select flds from notes'):
                f = raw.split('\x1f')
                if f[0] not in words or f[0] in samples: continue
                entry = next((e for e in manifest if (e['word'],e['reading']) == (f[0],f[1])), None)
                if not entry: continue
                filename = Path(entry['image']).stem + '.webp'
                data = image_bytes(ROOT / 'assets/card-visuals', entry)
                (out / filename).write_bytes(data)
                audio = re.search(r'\[sound:([^]]+)\]',f[8])
                audio_name = audio[1] if audio else None
                if audio_name: (out / audio_name).write_bytes(z.read(media[audio_name]))
                # Use the real recognition answer layout for Japanese + meaning + supporting material.
                values = dict(zip(fields, f))
                values['KanjiBreakdown'] = re.sub(r'<figure class="vocab-visual">.*?</figure>', '', f[7], flags=re.S)
                template = (ROOT / 'templates/recognition_back.html').read_text()
                template = template.replace('__RUNTIME__', runtime).replace('__TAP_GUARD__', '')
                content = renderer.render(template, values).replace('class="card tappable"', 'class="card tappable has-vocab-visual"')
                content = re.sub(r'\[sound:([^\]]+)\]', r'<a href="#" onclick="event.preventDefault();this.nextElementSibling.currentTime=0;this.nextElementSibling.play()">Play</a><audio src="\1"></audio>', content)
                for name in re.findall(r'src="([^"<>]+)"', content):
                    if name in media: (out / name).write_bytes(z.read(media[name]))
                for name, member in media.items():
                    if name.startswith('_kr_') and name.endswith('.mp3'):
                        (out / name).write_bytes(z.read(member))
                doc = '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><base href="media/"><style>' + css + '\nhtml,body{margin:0;padding:0;background:transparent}.card{padding-top:0;padding-bottom:16px;display:flow-root}.tap-shield{display:none}.word-block{cursor:pointer}\n</style></head><body>' + content + '</body></html>'
                samples[f[0]] = dict(word=f[0], reading=f[1], image='media/'+filename, audio='media/'+audio_name if audio_name else None, doc=doc)
assert len(samples) >= 3
(HERE / 'samples.js').write_text('const samples = '+json.dumps([samples[w] for w in words if w in samples],ensure_ascii=False)+';\n')
print('Built', len(samples), 'samples:', ', '.join(samples))
