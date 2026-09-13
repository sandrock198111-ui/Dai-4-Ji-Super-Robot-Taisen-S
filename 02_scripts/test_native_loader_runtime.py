"""Full-emulator regression and cache hit/miss checks for the current payload."""
import argparse,json,os,subprocess,sys,struct
from pathlib import Path
from run_font_switch_probe import compare

def main():
 ap=argparse.ArgumentParser()
 for k in ['evidence','output','core','font']:ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args();p=a.output.resolve();e=a.evidence.resolve()
 m=json.loads((p/'native_manifest.json').read_text(encoding='utf-8'));old=(p/'MAP_original.bin').read_bytes();new=(p/'MAP_native.bin').read_bytes()
 lo=m['start']-0x80106380;hi=m['end']-0x80106380
 code=dict(address=hex(m['start']),before=old[lo:hi].hex(),hex=new[lo:hi].hex())
 env=os.environ.copy();env.update(SRW_TEST_ROOT=str(e),SRW_CORE=str(a.core.resolve()))
 runner=Path(__file__).with_name('run_psx.py')
 def run(name,c):
  c['output']=str(p/name);cfg=p/(name+'.local.json');cfg.write_text(json.dumps(c))
  with (p/(name+'.log')).open('w') as f:subprocess.run([sys.executable,str(runner),str(e/'patched.cue'),str(cfg)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
  return (p/name/'ram.bin').read_bytes()
 regression={}
 for name in ['hold_base','redraw_base','restore_base2','map_hold_base','map_transition_base']:
  c=json.loads((e/(name+'.json')).read_text());c['initial_edits']=[code];run('regression_'+name,c)
  result=compare(e/name,p/('regression_'+name));assert result['vram_words']==0,(name,result);regression[name]=result
 needle=bytes.fromhex('f56ef35af3cbf574f4dff29a');baseline=(e/'controls/ram.bin').read_bytes();assert baseline.count(needle)==1;at=baseline.index(needle)
 native={}
 for name,indices in [('native_miss',[0,1]),('native_hit',[0,0]),('native_other',[4,5])]:
  encoded=b''.join(b'\xf0\x00GL'+struct.pack('<H',i) for i in indices);assert len(encoded)==len(needle)
  text=''.join(m['characters'][i] for i in indices)
  c=dict(load_state=str(e/'controls/state.bin'),frames=120,inputs=[[10,30,[3]]],captures=[40,120],dumps=[40,120],
   initial_edits=[code,dict(address=hex(0x80000000+at),before=needle.hex(),hex=encoded.hex())],reference_font=str(a.font.resolve()),
   pixel_checks=[dict(frame=40,text=text,x=56,y=96,color=[240,232,216])])
  ram=run(name,c);counters={k:struct.unpack_from('<I',ram,m[k]&0x1fffff)[0] for k in ['owner','misses','hits']}
  assert counters==dict(owner=indices[-1],misses=1 if indices[0]==indices[1] else 2,hits=1 if indices[0]==indices[1] else 0)
  assert ram[0x57838:0x63838]==baseline[0x57838:0x63838]
  assert ram[m['cache']&0x1fffff:(m['cache']&0x1fffff)+32]==ram[(m['library']&0x1fffff)+32*indices[-1]:(m['library']&0x1fffff)+32*(indices[-1]+1)]
  native[name]=dict(counters=counters,original_font_unchanged=True,pixel_check_passed=True)
 report=dict(regression=regression,native=native,modified_map_sha256=m['modified_map_sha256'],scope='Runtime code installation tests; cold boot is a separate check')
 (p/'full_emulator_regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
