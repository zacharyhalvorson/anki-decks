#!/usr/bin/env python3
"""Create a local gallery of generated artwork for semantic and alpha review."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / 'assets/card-visuals'
OUT = ROOT / 'experiments/card-visuals/build'
OUT.mkdir(exist_ok=True)
images = OUT / 'catalog-images'
if not images.exists():
    images.symlink_to(CAT / 'images', target_is_directory=True)
manifest = json.loads((CAT / 'manifest.json').read_text())
reviewed = {(e['word'], e['reading']): e['image'] for e in manifest}
queue = json.loads((CAT / 'generation-queue.json').read_text())
entries = []
for index, e in enumerate(queue):
    if not (CAT / 'images' / e['image']).exists():
        continue
    entries.append(dict(e, index=index, reviewed=reviewed.get((e['word'],e['reading'])) == e['image']))
data = json.dumps(entries, ensure_ascii=False).replace('</', '<\\/')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vocabulary artwork review</title><style>
body{font:16px system-ui;margin:24px;background:#eee;color:#222}header{position:sticky;top:0;background:#eee;padding:12px;z-index:1}button,input{font:inherit;margin:4px;padding:8px}main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}article{background:white;border:1px solid #bbb;border-radius:12px;overflow:hidden}h2,p{margin:10px 14px}h2{font-size:20px}p{font-size:13px}.art{background:#202020}.art img{display:block;width:100%;aspect-ratio:3/1;object-fit:contain}body.light .art{background:white}@media(max-width:800px){main{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:480px){main{grid-template-columns:1fr}}</style>
<header><strong>Vocabulary artwork review</strong> <input id="search" placeholder="Filter word"><label><input type="checkbox" id="pending">Pending only</label><button id="prev">Previous</button><button id="next">Next</button><label><input type="checkbox" id="light">White background</label><span id="count"></span></header><main id="grid"></main>
<script>const entries=__DATA__;let page=0;const search=document.querySelector('#search'),grid=document.querySelector('#grid');function draw(){const filtered=entries.filter(e=>(e.word+' '+e.reading+' '+e.index).includes(search.value)&&(!document.querySelector('#pending').checked||!e.reviewed));page=Math.max(0,Math.min(page,Math.ceil(filtered.length/12)-1));grid.replaceChildren();for(const e of filtered.slice(page*12,page*12+12)){const a=document.createElement('article');const h=document.createElement('h2');h.textContent=e.index+' · '+e.word+' ('+e.reading+')';const box=document.createElement('div');box.className='art';const img=document.createElement('img');img.src='catalog-images/'+encodeURIComponent(e.image);img.alt=e.alt;box.append(img);const p=document.createElement('p');p.textContent=e.reviewed?'Accepted in catalog':'Pending visual review';a.append(h,box,p);grid.append(a);}document.querySelector('#count').textContent=(page+1)+' / '+Math.max(1,Math.ceil(filtered.length/12))+' — '+filtered.length+' images';}search.oninput=()=>{page=0;draw()};document.querySelector('#pending').onchange=()=>{page=0;draw()};document.querySelector('#prev').onclick=()=>{page--;draw()};document.querySelector('#next').onclick=()=>{page++;draw()};document.querySelector('#light').onchange=e=>document.body.classList.toggle('light',e.target.checked);draw();</script></html>'''.replace('__DATA__',data)
(OUT/'review.html').write_text(page)
print(f'{len(entries)} generated assets: {OUT / "review.html"}')
