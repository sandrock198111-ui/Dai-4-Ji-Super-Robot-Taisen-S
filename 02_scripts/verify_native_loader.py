"""Execute original/new MIPS renderer and compare legacy behavior independently."""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'06_tools/python'))
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN
from unicorn.mips_const import *

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--ram',type=Path,required=True);a=ap.parse_args()
 p=a.output;m=json.loads((p/'native_manifest.json').read_text(encoding='utf-8'));ram=a.ram.read_bytes()
 machines=[]
 for name in ['MAP_original.bin','MAP_native.bin']:
  u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_write(0,ram);u.mem_write(0x106380,(p/name).read_bytes());machines.append(u)
 def prepare(u,gid,phase,payload=bytes(8)):
  for off,value in [(0x1a4f04,0x801d0000),(0x1a6dd8,phase),(0x1a6c9c,7),(0x1a50cc,0),(0x1a6b78,32),(0x1a6b74,0x80070001),
                    (0x1a4fb0,0xf),(0x1a4fb4,0xf0),(0x1a4fb8,0xf00),(0x1a4fbc,0xf000)]:u.mem_write(off,struct.pack('<I',value))
  u.mem_write(0x1a6e88,struct.pack('<H',0x4321));u.mem_write(0x1d0000,b'\xa5'*0x1000);u.mem_write(0x70001,payload)
  u.reg_write(UC_MIPS_REG_A0,gid);u.reg_write(UC_MIPS_REG_S0,0x12345678);u.reg_write(UC_MIPS_REG_SP,0x801ff000);u.reg_write(UC_MIPS_REG_RA,0x80010000)
 def run(u):
  u.emu_start(0x80110dbc,0x80010000,count=10000)
  assert u.reg_read(UC_MIPS_REG_PC)==0x80010000
  return (bytes(u.mem_read(0x1d0000,0x1000)),*[bytes(u.mem_read(off,4)) for off in [0x1a4f04,0x1a6dd8,0x1a6c9c,0x1a50cc]],u.reg_read(UC_MIPS_REG_SP),u.reg_read(UC_MIPS_REG_S0))
 count=0
 for gid in list(range(0xf0))+list(range(0x100,0x700)):
  for phase in [0,1]:
   out=[]
   for u in machines:prepare(u,gid,phase);out.append(run(u))
   assert out[0]==out[1],(hex(gid),phase)
   count+=1
 # Each virtual glyph must render exactly as an independently injected legacy
 # bitmap in the unmodified renderer. No target cache logic builds this oracle.
 virtual=0;u0,u1=machines
 original_slot=bytes(u0.mem_read(0x57858,32))
 for index in [0,0,1,2,3,4,5,5,0]:
  glyph=bytes(u1.mem_read((m['library']&0x1fffff)+32*index,32))
  for phase in [0,1]:
   u0.mem_write(0x57858,glyph);prepare(u0,0x101,phase)
   prepare(u1,0x100,phase,b'GL'+struct.pack('<H',index))
   assert run(u0)==run(u1),(index,phase)
   assert struct.unpack('<I',u1.mem_read(0x1a6b74,4))[0]==0x80070005
   virtual+=1
 u0.mem_write(0x57858,original_slot)
 # Invalid signatures and unsupported index preserve the legacy glyph route.
 for payload in [b'GX\x00\x00',b'GL\x06\x00',b'GL\xff\xff']:
  for u in machines:prepare(u,0x100,0,payload)
  assert run(u0)==run(u1)
  assert struct.unpack('<I',u1.mem_read(0x1a6b74,4))[0]==0x80070001
 for cursor in [0,0x1f801000,0x801ffffe,0x80200000,0xa0070001]:
  for u in machines:prepare(u,0x100,0);u.mem_write(0x1a6b74,struct.pack('<I',cursor))
  assert run(u0)==run(u1),hex(cursor)
 report=dict(legacy_cases=count,legacy_pixel_and_layout_mismatches=0,virtual_cases=virtual,virtual_mismatches=0,
  cache_misses=struct.unpack('<I',u1.mem_read(m['misses']&0x1fffff,4))[0],cache_hits=struct.unpack('<I',u1.mem_read(m['hits']&0x1fffff,4))[0],
  scope='MIPS function execution in Unicorn, not full-game proof')
 assert report['cache_misses']>0 and report['cache_hits']>0
 (p/'mips_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
