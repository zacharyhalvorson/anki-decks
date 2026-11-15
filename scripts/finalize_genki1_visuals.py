#!/usr/bin/env python3
"""Create opaque review sheets, then register only explicitly reviewed GENKI artwork."""
import json,hashlib,shutil,sys,collections
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'assets/genki1';CAT=ROOT/'assets/card-visuals'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
jobs=read(DATA/'image-jobs.json');records=read(DATA/'generated-records.json');audit=read(DATA/'visual-audit.json')
latest={}
for r in records:
 if not r.get('rejected') or r['word'] not in latest:latest[r['word']]=r
# Two initially flagged raw previews require explicit composited inspection.
for word in ['メニュー','飼う']:
 latest[word]=next(r for r in reversed(records) if r['word']==word)
if sys.argv[1]=='sheets':
 out=DATA/'visual-review';out.mkdir(exist_ok=True)
 font=ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',17)
 available=[j for j in jobs if j['word'] in latest]
 for start in range(0,len(available),20):
  batch=available[start:start+20];sheet=Image.new('RGB',(1600,310*((len(batch)+3)//4)),'#eee');draw=ImageDraw.Draw(sheet)
  for n,j in enumerate(batch):
   x=n%4*400;y=n//4*310;r=latest[j['word']];draw.text((x+5,y+3),j['word'],font=font,fill='black')
   im=Image.open(r['source']).convert('RGBA');im.thumbnail((390,130))
   for k,color in enumerate(['#ffffff','#202020']):
    bg=Image.new('RGBA',(390,130),color);bg.alpha_composite(im,((390-im.width)//2,(130-im.height)//2));sheet.paste(bg.convert('RGB'),(x+5,y+30+k*133))
  path=out/f'new-{start//20:02}.jpg';sheet.save(path,quality=95);print(path)
 print(len(available),'of',len(jobs));sys.exit()
assert sys.argv[1]=='register'
decisions=read(DATA/'visual-decisions.json');assert set(decisions)=={j['word'] for j in jobs}
manifest=read(CAT/'manifest.json');senses=read(CAT/'sense-overrides.json');prompts=read(CAT/'generation-prompts.json');selection=read(CAT/'image-production.json')
for j in jobs:
 r=latest[j['word']];digest=hashlib.sha256(Path(r['source']).read_bytes()).hexdigest();d=decisions[j['word']]
 assert d['sha256']==digest and d['accepted'] and d['reviewed_light_and_dark']
 shutil.copyfile(r['source'],CAT/'images'/j['image'])
 entry={k:j[k] for k in ['word','reading','image']};entry.update(alt=j['scene'],reason=d['reason'])
 target=senses if j.get('sense_override') else manifest
 if j.get('sense_override'):entry['meaning']=j['meaning']
 key=lambda e:tuple(e.get(k) for k in (['word','reading','meaning'] if j.get('sense_override') else ['word','reading']))
 target[:]=[e for e in target if key(e)!=key(entry)];target.append(entry)
 prompts[:]=[p for p in prompts if p.get('image')!=j['image']]
 prompts.append({**entry,'meaning':j['meaning'],'prompt':r['prompt'],'references':r['references'],'tool':r['tool'],'source':r['source'],'source_sha256':digest,'output':'assets/card-visuals/images/'+j['image'],'reviewed_light_and_dark':True,'question_reviewed':j['question']})
 if j['question']:
  s={k:j[k] for k in ['word','reading','meaning','image']};s['image_sha256']=digest
  selection['entries'][:]=[e for e in selection['entries'] if tuple(e[k] for k in ['word','reading','meaning'])!=tuple(s[k] for k in ['word','reading','meaning'])];selection['entries'].append(s)
 r.update(reviewed=True,rejected=False,image=j['image'])
byword={e['word']:e for e in manifest}
for row in audit:
 status=row['status']
 if status in ['review-reuse','generate-shared']:
  source=byword[row['source_word']];entry={'word':row['word'],'reading':row['reading'],'image':source['image'],'alt':source['alt'],'reason':'Reviewed on light and dark at card size for this GENKI sense; answer-side context only. '+row['meaning']}
  assert not any((e['word'],e['reading'])==(entry['word'],entry['reading']) for e in manifest)
  manifest.append(entry);row.update(status='reviewed-reuse',image=entry['image'],reason=entry['reason'])
 elif status=='generate':row.update(status='reviewed-new',reason=decisions[row['word']]['reason'])
 elif status=='review-existing':row.update(status='reviewed-existing',reason='Existing packaged scene reviewed at card size against the exact GENKI meaning.')
 elif status=='text-only':
  word=row['word']
  if '〜' in word or word in {'一時間','二三日','年上','Ｌサイズ'}:why='A grammatical attachment, counter, quantity, or relational expression needs its written linguistic context.'
  elif word in {'インフルエンザ'}:why='A generic sick-person scene cannot distinguish influenza from a cold or other illness.'
  elif word in {'今学期','来学期','今度','後で','このごろ','週末','もうすぐ','時'}:why='An unlabeled calendar or clock would not identify this exact time expression.'
  else:why='An unlabeled scene would be ambiguous for this discourse, degree, question, or abstract expression; two examples carry the meaning.'
  row['reason']=why
for path,data in [(CAT/'manifest.json',manifest),(CAT/'sense-overrides.json',senses),(CAT/'generation-prompts.json',prompts),(CAT/'image-production.json',selection),(DATA/'generated-records.json',records),(DATA/'visual-audit.json',audit)]:write(path,data)
print(dict(collections.Counter(r['status'] for r in audit)));print('Catalog',len(manifest),'senses',len(senses),'selected',len(selection['entries']))
