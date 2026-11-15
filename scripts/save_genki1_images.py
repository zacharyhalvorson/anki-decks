#!/usr/bin/env python3
"""Save generated illustration outputs and actual prompts; registration is separate."""
import json,sys,shutil,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/genki1';CAT=ROOT/'assets/card-visuals'
rows=json.loads((OUT/'visual-audit.json').read_text());jobs={r['word']:r for r in rows if r['status']=='generate'}
if sys.argv[1]=='--jobs':
 scenes=dict(line.split('|',1) for line in (OUT/'visual-scenes.psv').read_text().splitlines())
 result=[]
 for word,row in jobs.items():
  result.append({**row,'scene':scenes[word],'question':word in {'スマホ','ピザ','トマト','ハンバーガー','すし','新幹線'}})
 (OUT/'image-jobs.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(len(result));sys.exit()
records=json.loads(sys.argv[1]);path=OUT/'generated-records.json';old=json.loads(path.read_text()) if path.exists() else []
for rec in records:
 if any(x['source']==rec['source'] for x in old):continue
 source=Path(rec['source']).resolve();assert source.is_relative_to(Path.home()/'.codex/generated_images') and source.suffix=='.png'
 job=jobs[rec['word']];im=Image.open(source);assert im.mode=='RGBA' and im.getchannel('A').getextrema()==(0,255)
 rec['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();rec['dimensions']=im.size
 rec['references']=rec.get('references') or ['vocab-330471442ce4-v2.png','vocab-fdf9d40719eb.png'];rec['tool']='image_gen';rec['reviewed']=False
 if not rec.get('rejected'):
  destination=CAT/'images'/job['image']
  if destination.exists():
   prior=OUT/'visual-review'/('superseded-'+rec['source_sha256'][:8]+'.png');shutil.copyfile(destination,prior)
  shutil.copyfile(source,destination);rec['image']=job['image']
 old.append(rec)
path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n');print('Saved',len(records),'records;',len(old),'total attempts')
