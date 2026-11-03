"""Attach the reviewed illustration catalog by exact word + reading, without schema changes."""
import hashlib
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path

FIGURE = re.compile(r'<figure class="vocab-visual">.*?</figure>', re.S)

def image_bytes(catalog, entry):
    """Keep original artwork; package a small transparent copy for card display."""
    source = catalog / 'images' / entry['image']
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    optimized = catalog / 'optimized' / (digest + '.webp')
    if not optimized.exists():
        optimized.parent.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=optimized.parent, suffix='.tmp.webp', delete=False) as handle:
            temporary = Path(handle.name)
        try:
            subprocess.run(['cwebp', '-quiet', '-q', '85', '-m', '6',
                            '-resize', '1200', '0', str(source), '-o', str(temporary)], check=True)
            temporary.replace(optimized)
        finally:
            temporary.unlink(missing_ok=True)
    return optimized.read_bytes()

def apply_visuals(con, media, root, now):
    catalog = Path(root) / 'assets/card-visuals'
    entries = json.loads((catalog / 'manifest.json').read_text())
    lookup = {(e['word'], e['reading']): e for e in entries}
    assert len(lookup) == len(entries), 'duplicate illustration keys'
    added, illustrated, changed = {}, 0, 0
    models = json.loads(con.execute('select models from col').fetchone()[0])
    for nid, mid, fields, modified in con.execute('select id, mid, flds, mod from notes').fetchall():
        names = [f['name'] for f in models[str(mid)]['flds']]
        assert names[:3] == ['Word', 'Reading', 'Meaning'] and names[7] == 'KanjiBreakdown'
        f = fields.split('\x1f')
        entry = lookup.get((f[0], f[1]))
        if entry is None:
            continue
        blob = image_bytes(catalog, entry)
        filename = 'vocab_visual_' + hashlib.sha256(blob).hexdigest()[:16] + '.webp'
        if filename not in media.values():
            index = str(max(map(int, media), default=-1) + 1)
            media[index] = filename
            added[index] = blob
        figure = '<figure class="vocab-visual"><img src="' + filename + '" alt="' + html.escape(entry['alt'], quote=True) + '"></figure>'
        f[7] = figure + FIGURE.sub('', f[7])
        updated = '\x1f'.join(f)
        if updated != fields:
            con.execute('update notes set flds=?, mod=?, usn=-1 where id=?', (updated, max(now, modified + 1), nid))
            changed += 1
        illustrated += 1
    return added, illustrated, changed
