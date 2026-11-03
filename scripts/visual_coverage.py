#!/usr/bin/env python3
"""Report actual illustrated-note coverage in the five canonical deck exports."""
import json, sqlite3, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DECKS = ['GENKI I Vocab','GENKI II Vocab','JLPT N4','JLPT N5','Quartet I Vocab']
manifest = json.loads((ROOT / 'assets/card-visuals/manifest.json').read_text())
keys = {(e['word'],e['reading']) for e in manifest}
assert len(keys) == len(manifest)
report = {'catalog_entries':len(keys),'unique_images':len({e['image'] for e in manifest}),'decks':{}}
for deck in DECKS:
    with tempfile.TemporaryDirectory() as temp, zipfile.ZipFile(ROOT / (deck+'.apkg')) as archive:
        archive.extract('collection.anki21',temp)
        con=sqlite3.connect(Path(temp)/'collection.anki21')
        notes=[row[0].split('\x1f') for row in con.execute('select flds from notes')]
        actual=sum('<figure class="vocab-visual">' in f[7] for f in notes)
        available=sum(tuple(f[:2]) in keys for f in notes)
        report['decks'][deck]={'notes':len(notes),'illustrated':actual,'catalog_matches':available,'pending_build':available-actual}
        con.close()
print(json.dumps(report,ensure_ascii=False,indent=2))
