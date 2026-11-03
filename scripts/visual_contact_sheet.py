#!/usr/bin/env python3
"""Render a temporary review sheet; never changes source illustrations."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'assets/card-visuals'
q=json.loads((p/'generation-queue.json').read_text())
indices=[int(x) for x in sys.argv[1].split(',')]
font=ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',18)
sheet=Image.new('RGB',(1600,210*((len(indices)+3)//4)), '#eeeeee');draw=ImageDraw.Draw(sheet)
for n,i in enumerate(indices):
 e=q[i];x=n%4*400;y=n//4*210
 draw.text((x+8,y+4),str(i)+' '+e['word'],font=font,fill='#111111')
 if not (p/'images'/e['image']).exists():
  draw.text((x+8,y+60),'Pending generation',font=font,fill='#555555');continue
 im=Image.open(p/'images'/e['image']).convert('RGBA');im.thumbnail((384,140))
 draw.rectangle((x+8,y+34,x+392,y+174),fill='#202020');sheet.paste(im,(x+8+(384-im.width)//2,y+34+(140-im.height)//2),im)
 draw.text((x+8,y+180),e['alt'].replace('Illustration of ','')[:42],font=font,fill='#111111')
out=Path('/tmp/anki-review-'+str(indices[0])+'.jpg');sheet.save(out,quality=92);print(out)
