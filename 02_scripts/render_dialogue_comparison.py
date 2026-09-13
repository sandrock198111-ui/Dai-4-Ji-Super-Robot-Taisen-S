"""Render selected paired record glyphs from original font bytes, not runtime screenshots. Dynamic names remain placeholders."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
w=Path(__file__).resolve().parents[1]/'01_work/translation_comparison';rows=json.loads((w/'candidate_records.local.json').read_text(encoding='utf-8'));fonts={l:(w/f'stay_{l}.bin').read_bytes() for l in ['ja','ko']}
def render(rec,lang):
 im=Image.new('RGB',(640,400),'black');dr=ImageDraw.Draw(im);x=0;y=0
 for t in rec[lang]['tokens']:
  g=t['g']
  if g is None:
   if t['op'] in [246,247]:x=0;y+=20
   elif t['op']==251:
    dr.text((x,y+2),'[NAME]',fill='yellow');x+=48
   continue
  width=8 if g<256 else 16
  if x+width>620:x=0;y+=20
  at=0x36838+g*16 if g<256 else 0x37838+(g-256)*32
  b=fonts[lang][at:at+width*2]
  for yy in range(16):
   for xx in range(width):
    if b[(xx//8)*16+yy]&(128>>(xx%8)):im.putpixel((x+xx,y+yy),(255,255,255))
  x+=width
 return im.crop((0,0,640,y+20))
selected=[x for x in rows if x['h']==2 and 186<=x['e']<=226]
for base in range(0,len(selected),5):
 cards=[]
 for x in selected[base:base+5]:
  a=render(x,'ja');b=render(x,'ko');im=Image.new('RGB',(1280,max(a.height,b.height)+30),(35,35,35));ImageDraw.Draw(im).text((4,4),f"H02 E{x['e']} | JA left / KO right",fill='yellow');im.paste(a,(0,25));im.paste(b,(640,25));cards.append(im)
 board=Image.new('RGB',(1280,sum(i.height for i in cards)));y=0
 for im in cards:board.paste(im,(0,y));y+=im.height
 board.save(w/f'records_{base//5:02}.png')
print([(x['e'],x['ko_text'][:70]) for x in selected])
