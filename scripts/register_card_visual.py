#!/usr/bin/env python3
"""Register one completed built-in image generation without touching Anki exports."""
import json, shutil, sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'assets/card-visuals'
index, source = int(sys.argv[1]), Path(sys.argv[2])
jobs = json.loads((CATALOG / 'generation-queue.json').read_text())
job = jobs[index]
with Image.open(source) as image:
    assert image.width > image.height, 'expected landscape composition'
    assert image.mode == 'RGBA' and image.getextrema()[3][0] == 0, 'expected transparent background'
filename = job['image']
dest = CATALOG / 'images' / filename
if dest.exists():
    assert dest.read_bytes() == source.read_bytes(), f'will not overwrite {dest}'
else:
    shutil.copyfile(source, dest)
manifest = json.loads((CATALOG / 'manifest.json').read_text())
assert job.get('replace_existing') or not any((e['word'],e['reading']) == (job['word'],job['reading']) for e in manifest)
manifest = [e for e in manifest if (e['word'],e['reading']) != (job['word'],job['reading'])]
manifest.append({k:job[k] for k in ['word','reading','image','alt','reason']})
(CATALOG / 'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
prompts = json.loads((CATALOG / 'generation-prompts.json').read_text())
prompts.append(dict(job,tool='built-in image_gen',source=str(source)))
(CATALOG / 'generation-prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2)+'\n')
coverage = json.loads((CATALOG / 'coverage.json').read_text())
for entry in coverage:
    if (entry['word'],entry['reading']) == (job['word'],job['reading']): entry['illustrated'] = True
(CATALOG / 'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'word':job['word'],'path':str(dest),'entries':len(manifest)},ensure_ascii=False))
