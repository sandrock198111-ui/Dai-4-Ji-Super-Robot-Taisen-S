"""Compare paired full-emulator runs; never edits an emulator or game image."""
from pathlib import Path
import hashlib,json,struct,os
from collections import Counter
from PIL import Image,ImageChops,ImageDraw

ROOT=Path(os.environ['SRW_TEST_ROOT']).resolve()
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def vram(path):
 data=path.read_bytes();tag=b'&GPURAM[0][0]'
 assert data.count(tag)==1
 at=data.index(tag)+len(tag);size=struct.unpack_from('<I',data,at)[0]
 assert size==1024*512*2
 return data[at+4:at+4+size]
def compare(a,b,stem='state'):
 state_name='state.bin' if stem=='state' else stem+'.state'
 image_name='last.png' if stem=='state' else stem+'.png'
 va,vb=[vram(ROOT/x/state_name) for x in [a,b]]
 indices=[i//2 for i in range(0,len(va),2) if va[i:i+2]!=vb[i:i+2]]
 ia,ib=[Image.open(ROOT/x/image_name).convert('RGB') for x in [a,b]]
 diff=ImageChops.difference(ia,ib)
 pages=Counter((i%1024//64,i//1024//256) for i in indices)
 return dict(baseline=a,modified=b,sample=stem,vram_different_words=len(indices),
  screen_diff_bbox=diff.getbbox(),screen_different_pixels=sum(p!=(0,0,0) for p in diff.get_flattened_data()),
  changed_64word_256line_tiles={f'{x},{y}':n for (x,y),n in sorted(pages.items())})
cases=[compare(a,b) for a,b in [('hold_base','hold_blank'),('redraw_base','redraw_blank'),
 ('restore_base2','restore_blank2'),('map_hold_base','map_hold_blank'),
 ('map_transition_base','map_transition_blank')]]
cases += [compare('battle_base','battle_blank',f'f{n:06}') for n in [1,30,60,120,300,600,900]]
assert cases[0]['vram_different_words']==0
assert cases[1]['screen_different_pixels']>0
assert cases[2]['screen_different_pixels']==0
assert cases[3]['vram_different_words']==0
assert cases[4]['screen_different_pixels']>0
assert cases[5]['vram_different_words']==0
assert next(c for c in cases if c['sample']=='f000300')['screen_different_pixels']>0
report=dict(method='Same serialized full-emulator state and frame/input schedule; only 48KiB RAM font differs.',
 emulator='Existing mednafen_psx_libretro.dll, software GPU, native resolution, interpreter',
 core_sha256=sha(Path(os.environ['SRW_CORE'])),
 bios_sha256=sha(ROOT/'system/scph5500.bin'),
 bios_caveat='Existing firmware SHA1 213da1cb149b564c0ccb0b12e62d04df367ac851 differs from core expected b05def971d8ec59f346f2d9ac21fb742e3eb6917. Independent supported-BIOS rerun remains required.',
 mutation=dict(address='0x80057838',bytes=49152,kind='diagnostic zero bitmap; process RAM only'),
 cases=cases,full_game_vram_safety_proven=False,cache_implemented=False,
 disc_hashes={p.name:sha(p) for p in ROOT.parent.glob('*Track 1*.bin')})
(ROOT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
sheet=Image.new('RGB',(640,3*270),(28,28,28));draw=ImageDraw.Draw(sheet)
for row,(a,b,title) in enumerate([
 ('hold_base/last.png','hold_blank/last.png','Existing text after RAM font replacement: identical'),
 ('map_transition_base/last.png','map_transition_blank/last.png','New map text: changed; portrait/background preserved'),
 ('battle_base/f000300.png','battle_blank/f000300.png','New battle text: changed; sprites/effects preserved')]):
 draw.text((8,row*270+4),title,fill='white')
 for col,p in enumerate([a,b]):
  im=Image.open(ROOT/p).convert('RGB');im.thumbnail((288,240))
  sheet.paste(im,(col*320+32,row*270+24))
sheet.save(ROOT/'comparison.png')
print(json.dumps(cases,ensure_ascii=False,indent=2))
