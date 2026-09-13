"""Six existing slots, many new syllables; independent restored-state samples.

Not a disc patch or in-game cache. Retains baseline font appearance and text
control flow. Each page independently starts from the same diagnostic state.
"""
import argparse,json,os,subprocess,sys,hashlib
from pathlib import Path
from PIL import ImageFont
from build_font_probe import raster

def main():
 ap=argparse.ArgumentParser()
 for x in ['evidence','font','output','core']:ap.add_argument('--'+x,type=Path,required=True)
 ap.add_argument('--mapping',type=Path,help='Deprecated; identities now reconstructed directly from baseline RAM')
 ap.add_argument('--count',type=int,default=1800);a=ap.parse_args()
 assert 0<a.count<=9000 and a.count%6==0
 for x in ['evidence','font','output','core']:setattr(a,x,getattr(a,x).resolve())
 a.output.mkdir(parents=True,exist_ok=True)
 original_text='주인공설정을';ids=[]
 ram=(a.evidence/'controls/ram.bin').read_bytes();bank=ram[0x57838:0x63838]
 font=ImageFont.truetype(str(a.font),12)
 for ch in original_text:
  shape=raster(font,ch);matches=[0x100+i//32 for i in range(0,len(bank),32) if bank[i:i+32]==shape]
  assert len(matches)==1,(ch,matches)
  ids.append(matches[0])
 for ch,gid in zip(original_text,ids):assert bank[(gid-0x100)*32:(gid-0x100+1)*32]==raster(font,ch)
 existing={bank[i:i+32] for i in range(0,len(bank),32)};glyphs=[];seen=set()
 preferred='넋뛴샘샴띠뜬끈덫'
 for ch in dict.fromkeys(preferred+''.join(chr(cp) for cp in range(0xac00,0xd7a4))):
  shape=raster(font,ch)
  if shape in existing or shape in seen or not any(shape):continue
  if any(shape[16+y]&31 for y in range(16)) or any(shape[x] for x in [0,1,2,14,15,16,17,18,30,31]):continue
  seen.add(shape);glyphs.append((ch,shape))
  if len(glyphs)==a.count:break
 assert len(glyphs)==a.count
 env=os.environ.copy();env.update(SRW_TEST_ROOT=str(a.evidence),SRW_CORE=str(a.core))
 baseline=dict(output=str(a.output/'baseline'),load_state=str(a.evidence/'controls/state.bin'),frames=100,
  inputs=[[10,30,[3]]],captures=[40,60],pixel_checks=[dict(frame=t,text=original_text,x=56,y=96,color=[240,232,216]) for t in [40,60]],reference_font=str(a.font))
 baseline_path=a.output/'baseline.local.json';baseline_path.write_text(json.dumps(baseline))
 with (a.output/'baseline.log').open('w') as log:
  subprocess.run([sys.executable,str(Path(__file__).with_name('run_psx.py')),str(a.evidence/'patched.cue'),str(baseline_path)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 config=dict(output=str(a.output/'run'),load_state=str(a.evidence/'controls/state.bin'),
  frames=(a.count//6)*100,inputs=[],edits=[],captures=[],dumps=[],pixel_checks=[],reference_font=str(a.font),reset_state_frames=[])
 page_texts=[]
 for page in range(a.count//6):
  start=page*100;items=glyphs[page*6:page*6+6];text=''.join(ch for ch,g in items);page_texts.append(text)
  if page:config['reset_state_frames'].append(start)
  loads=[];restores=[]
  for gid,(ch,shape) in zip(ids,items):
   address=0x80057838+(gid-0x100)*32;old=ram[address&0x1fffff:(address&0x1fffff)+32]
   loads.append(dict(address=hex(address),before=old.hex(),hex=shape.hex()))
   restores.append(dict(address=hex(address),before=shape.hex(),hex=old.hex()))
  config['edits'] += [dict(frame=start+1,writes=loads),dict(frame=start+50,writes=restores)]
  config['inputs'] += [[start+10,start+30,[3]]]
  for t in [40,60]:config['pixel_checks'].append(dict(frame=start+t,text=text,x=56,y=96,color=[240,232,216],reference_screen=str(a.output/'baseline'/f'frame_{t:06}.png')))
  if page in [0,1,a.count//6-1]:
   config['captures'] += [start+40,start+60]
   config['dumps'] += [start+40,start+60]
 path=a.output/'stream.local.json';path.write_text(json.dumps(config),encoding='utf-8')
 with (a.output/'run.log').open('w') as log:
  subprocess.run([sys.executable,str(Path(__file__).with_name('run_psx.py')),str(a.evidence/'patched.cue'),str(path)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 result=json.loads((a.output/'run/run.json').read_text());final_ram=(a.output/'run/ram.bin').read_bytes()
 assert final_ram[0x57838:0x63838]==bank
 assert len(result['pixel_checks'])==a.count//3
 report=dict(scope='independent restored-state UI samples; external RAM provider, no in-game loader or continuous menu-transition claim',
  distinct_new_syllables=a.count,simultaneous_reused_slots=6,slot_ids=[hex(i) for i in ids],
  typeface='Galmuri11 regular v2.24.29 at baseline raster settings',
  font_sha256=hashlib.sha256(a.font.read_bytes()).hexdigest(),
  checks=len(result['pixel_checks']),pixel_mismatches=sum(x['mismatches'] for x in result['pixel_checks']),
  outside_text_pixel_mismatches=sum(x['outside_mismatches'] for x in result['pixel_checks']),
  complete_original_font_restored=True,frames=result['frames'],pages=page_texts,
  bios_caveat='Same prior core/unsupported-firmware hash; supported BIOS rerun pending')
 (a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='pages'},indent=2))

if __name__=='__main__':main()
