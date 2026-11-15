"""Preview actual packaged templates in a persistent browser frame."""
import importlib.util,json,re,sqlite3,tempfile,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('renderer',ROOT/'experiments/card-visuals/build.py');renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
media_dir=HERE/'media';media_dir.mkdir(exist_ok=True);samples=[]
for deck,words in [('GENKI I Vocab',['コンピューター','専攻']),('GENKI II Vocab',['階段','ひげ','財布']),('JLPT N4',['猫','意味']),('JLPT N5',['りんご']),('Quartet I Vocab',['桜'])]:
 with zipfile.ZipFile(ROOT/(deck+'.apkg')) as z,tempfile.TemporaryDirectory() as tmp:
  z.extract('collection.anki21',tmp);db=sqlite3.connect(tmp+'/collection.anki21');models=json.loads(db.execute('select models from col').fetchone()[0]);media=json.loads(z.read('media'))
  for mid,raw in db.execute('select mid,flds from notes'):
   f=raw.split('\x1f')
   if f[0] not in words:continue
   model=models[str(mid)];fields=dict(zip([v['name'] for v in model['flds']],f));template=next(t for t in model['tmpls'] if t['name']=='Production');sample={'label':deck+' · '+f[0]}
   for side in ['qfmt','afmt']:
    content=renderer.render(template[side],fields)
    content=re.sub(r'\[sound:([^\]]+)\]',r'<a href="#" onclick="event.preventDefault();this.nextElementSibling.currentTime=0;this.nextElementSibling.play()">Play</a><audio src="\1"></audio>',content)
    sample[side]='<!doctype html><html><head><meta charset="utf-8"><base href="media/"><style>'+model['css']+'</style></head><body>'+content+'</body></html>'
   samples.append(sample)
   needed=set(re.findall(r'(?:src="|\[sound:)([^"\]]+)',raw))
   needed.update(re.findall(r'src="(_kanji_strokes[^" ]+)"',template['afmt']))
   for member,name in media.items():
    if name in needed or name.startswith('_kr_'):(media_dir/name).write_bytes(z.read(member))
page='''<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Packaged image cards</title><style>body{font:15px system-ui;background:#f4f3ef;margin:24px}header{max-width:600px;margin:auto}button,select{font:inherit;padding:10px;margin:4px}iframe{display:block;width:100%;max-width:600px;border:0;margin:20px auto;background:white}body.phone iframe{max-width:375px}</style><header><h2>Actual packaged cards</h2><p>Production cards extracted from the updated decks.</p><select id="sample" aria-label="Card sample"></select><button id="flip">Show answer</button><label><input id="phone" type="checkbox">Phone width</label></header><iframe id="frame" title="Packaged Anki card"></iframe><script>
const samples=__SAMPLES__;const select=document.querySelector('#sample'),frame=document.querySelector('#frame'),flip=document.querySelector('#flip');let answer=false,observer;for(let i=0;i<samples.length;i++)select.add(new Option(samples[i].label,i));
function size(){frame.style.height=(frame.contentDocument.body.getBoundingClientRect().height+24)+'px'}function observe(){observer?.disconnect();observer=new ResizeObserver(size);observer.observe(frame.contentDocument.body);size()}
function draw(){let doc=samples[select.value||0][answer?'afmt':'qfmt'];if(frame.contentDocument?.querySelector('.card')){const parsed=new DOMParser().parseFromString(doc,'text/html');const live=frame.contentDocument;live.head.innerHTML=parsed.head.innerHTML;live.body.replaceChildren(...Array.from(parsed.body.childNodes).map(n=>live.importNode(n,true)));live.querySelectorAll('script').forEach(old=>{const fresh=live.createElement('script');for(const a of old.attributes)fresh.setAttribute(a.name,a.value);fresh.textContent=old.textContent;old.replaceWith(fresh)});observe()}else{frame.srcdoc=doc}flip.textContent=answer?'Show question':'Show answer';if(answer){const audio=frame.contentDocument?.querySelector('.word-audio-hidden audio');audio?.play().catch(()=>{})}}
select.onchange=()=>{answer=false;draw()};flip.onclick=()=>{answer=!answer;draw()};document.querySelector('#phone').onchange=e=>document.body.classList.toggle('phone',e.target.checked);frame.onload=observe;draw();</script></html>'''
(HERE/'packaged.html').write_text(page.replace('__SAMPLES__',json.dumps(samples,ensure_ascii=False).replace('</','<\\/')))
print('Built',len(samples),'packaged samples')
