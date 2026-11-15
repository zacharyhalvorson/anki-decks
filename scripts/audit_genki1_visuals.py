#!/usr/bin/env python3
"""Inventory every GENKI I sense; preserve explicit reuse and text-only decisions."""
import json,re,sys,sqlite3,zipfile,collections
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).parent));import build_genki1 as b
ROOT=b.ROOT;CAT=ROOT/'assets/card-visuals';OUT=ROOT/'assets/genki1'
manual={'眼鏡':'めがね','けんかする':'喧嘩する','明後日':'あさって','おなか':'お腹','やせる':'痩せる','やせています':'痩せる','太っています':'太る','教師':'先生','男の人':'男','女の人':'女','警察官':'警官','熱がある':'熱','一人で':'一人','運動する':'運動','ドライブ':'運転する','有名人':'有名','シャワーを浴びる':'浴びる','たばこを吸う':'吸う','風邪を引く':'風邪','残念ですね':'残念','元気がない':'疲れる','スポーツ選手':'選手','歌手':'歌う','興味がある':'興味','歩いて':'歩く','カフェ':'喫茶店','やさしい':'易しい','早く／速く':'早い','知っています':'知る','いい':'良い','遅くなる':'遅れる','遅刻する':'遅れる','遅く':'遅れる'}
text=set('〜年生 〜さん 〜語 〜番 Ｌサイズ 〜か月 もうすぐ ところで 週末 〜週間 〜まで すごく どっち／どちら いい子 〜人 〜だけ どのぐらい そう 単語 〜ぐらい 〜後 〜が 今度 別に 年上 そうですね みんなで 〜円 〜年 〜枚 よかったら 是非 〜と 本当ですか 〜度 〜点 〜代 何か 〜ごろ 今学期 結構です 〜について 知りません できるだけ 何も 〜時間 どうですか 後で このごろ 来学期 〜から まあまあ じゃあ もちろん 時 ううん 〜か〜 それに 〜で どうやって うん 二三日 一時間 インフルエンザ'.split())
shared={'せきが出る':'せき','遅くなる':'遅刻する','遅く':'遅刻する','ホストファミリー':'ホームステイ'}
def norm(t):return b.hira(re.sub(r'[〜～\s()（）]','',re.sub(r'[(（][なの][)）]$','',t)))

def audit():
 manifest=json.loads((CAT/'manifest.json').read_text());byword={e['word']:e for e in manifest}
 z,c,media=b.read_deck(b.DECK_DIR/'GENKI I Vocab.apkg');members={v:k for k,v in media.items()};rows=[];pictures=[]
 for nid,tags,raw in c.execute('select id,tags,flds from notes order by tags,id'):
  f=raw.split(chr(31));e=next((x for x in manifest if x['word']==f[0] and x['reading']==f[1]),None)
  row={'nid':nid,'word':f[0],'reading':f[1],'meaning':f[2],'lesson':next(t for t in tags.split() if t.startswith('genki-'))}
  image=re.search(r'<figure class="vocab-visual"><img src="([^"]+)"',f[7])
  if f[0] in {'前','取る'}:
   row.update(status='generate',image='genki1-sense-'+str(nid)+'.png',sense_override=True,reason='Existing general artwork illustrates a different sense: temporal before / taking an object.')
  elif image:
   row.update(status='review-existing',image=e['image'] if e else None,packaged_image=image[1]);pictures.append((row,z.read(members[image[1]])))
  elif f[0] in text:row.update(status='text-only',reason='Grammar, time, quantity, discourse, or a meaning that an unlabeled picture would not distinguish reliably.')
  else:
   candidate=byword.get(manual.get(f[0],''))
   if not candidate:candidate=next((x for x in manifest if norm(x['word'])==norm(f[0]) and norm(x['reading'])==norm(f[1])),None)
   if candidate:row.update(status='review-reuse',source_word=candidate['word'],image=candidate['image'],source_alt=candidate['alt'])
   elif f[0] in shared:row.update(status='generate-shared',source_word=shared[f[0]])
   else:row.update(status='generate',image='genki1-'+str(nid)+'.png')
  rows.append(row)
 out=OUT/'visual-review';out.mkdir(exist_ok=True)
 font=ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',17)
 import io
 for start in range(0,len(pictures),64):
  entries=pictures[start:start+64];sheet=Image.new('RGB',(1600,210*((len(entries)+3)//4)),'#eee');draw=ImageDraw.Draw(sheet)
  for n,(row,blob) in enumerate(entries):
   x=n%4*400;y=n//4*210;draw.text((x+8,y+2),str(start+n)+' '+row['word'],font=font,fill='#111')
   im=Image.open(io.BytesIO(blob)).convert('RGBA');im.thumbnail((384,130));draw.rectangle((x+8,y+32,x+392,y+166),fill='#202020');sheet.paste(im,(x+8+(384-im.width)//2,y+32+(134-im.height)//2),im)
   draw.text((x+8,y+171),row['meaning'][:43],font=font,fill='#111')
  sheet.save(out/('existing-%02d.jpg'%(start//64)),quality=90)
 (OUT/'visual-audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(dict(collections.Counter(r['status'] for r in rows)))
 print('GENERATE',[(r['word'],r['meaning']) for r in rows if r['status']=='generate'])
 z.close();c.close()
if __name__=='__main__':audit()
