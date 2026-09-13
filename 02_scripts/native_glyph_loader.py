"""Build a bounded MAP renderer escape + one-entry RAM glyph cache prototype.

Code/data replace a duplicated renderer body, never an assumed empty RAM area.
Fonts and script control flow remain untouched unless --demo changes one literal.
"""
import argparse,json,struct,sys,hashlib
from pathlib import Path
from PIL import ImageFont
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
from build_font_probe import raster
from probe_extension_structure import inspect

BASE=0x80106380;START=0x80111034;END=0x80111298
MID=0x80111298;COMMON=0x801112b8
REG={'zero':0,'v0':2,'v1':3,'a0':4,'a1':5,'a2':6,'a3':7}

class Asm:
 def __init__(self):self.ops=[];self.labels={}
 @property
 def pc(self):return START+len(self.ops)*4
 def label(self,name):self.labels[name]=self.pc
 def i(self,op,rt,rs,imm):self.ops.append((op,rt,rs,imm))
 def r(self,op,rd,rs,rt):self.ops.append((op,rd,rs,rt))
 def j(self,target):self.ops.append(('j',target))
 def nop(self):self.ops.append(('nop',))
 def words(self):
  out=[]
  for n,x in enumerate(self.ops):
   op=x[0];pc=START+4*n
   if op=='nop':word=0
   elif op=='j':word=(2<<26)|((self.labels.get(x[1],x[1])>>2)&0x3ffffff)
   elif op in ['addu','sltu']:word=(REG[x[2]]<<21)|(REG[x[3]]<<16)|(REG[x[1]]<<11)|(0x21 if op=='addu' else 0x2b)
   elif op=='sll':word=(REG[x[2]]<<16)|(REG[x[1]]<<11)|(x[3]<<6)
   else:
    code={'ori':13,'andi':12,'lui':15,'addiu':9,'sltiu':11,'lw':35,'lbu':36,'sw':43,'beq':4,'bne':5}[op]
    imm=self.labels.get(x[3],x[3])
    if op in ['beq','bne']:
     assert (imm-pc-4)%4==0;imm=(imm-pc-4)//4;assert -32768<=imm<=32767
    word=(code<<26)|(REG[x[2]]<<21)|(REG[x[1]]<<16)|(imm&65535)
   out.append(word)
  return struct.pack('<'+'I'*len(out),*out)

def assemble(glyphs):
 a=Asm()
 a.i('ori','v0','zero',0x100);a.i('beq','v0','v1','escape');a.nop()
 a.i('sltiu','v0','v1',0x500);a.i('bne','zero','v0',MID);a.nop()
 a.i('lui','v0','zero',0x8016);a.i('lw','v0','v0',-0xcfc);a.nop()
 a.i('lw','a2','v0',8);a.i('addiu','v0','v1',-0x500);a.r('sll','v0','v0',5)
 a.r('addu','a2','a2','v0');a.j(COMMON);a.i('ori','a3','zero',0)
 a.label('escape')
 a.i('lui','v0','zero',0x801a);a.i('lw','a1','v0',0x6b74);a.nop()
 # A legacy glyph 0x100 can be drawn outside an active text stream. Do not
 # dereference a null, peripheral or end-of-RAM cursor in that case.
 a.i('lui','a0','zero',0x8000);a.r('sltu','a2','a1','a0');a.i('bne','zero','a2',MID);a.nop()
 a.i('lui','a0','zero',0x8020);a.i('addiu','a0','a0',-4);a.r('sltu','a2','a1','a0');a.i('beq','zero','a2',MID);a.nop()
 a.i('lbu','a0','a1',0);a.i('ori','a2','zero',0x47);a.i('bne','a2','a0',MID);a.nop()
 a.i('lbu','a0','a1',1);a.i('ori','a2','zero',0x4c);a.i('bne','a2','a0',MID);a.nop()
 a.i('lbu','a0','a1',2);a.i('lbu','a2','a1',3);a.nop();a.r('sll','a2','a2',8)
 a.r('addu','a0','a0','a2');a.i('sltiu','a2','a0',len(glyphs));a.i('beq','zero','a2',MID);a.nop()
 a.i('addiu','a1','a1',4);a.i('sw','a1','v0',0x6b74)
 # Position-independent within the reclaimed block, filled after code layout.
 a.i('lui','a3','zero',0x8011);owner_load=len(a.ops);a.i('lw','a2','a3',0);a.nop()
 a.i('beq','a0','a2','hit');a.nop()
 owner_store=len(a.ops);a.i('sw','a0','a3',0)
 miss_load=len(a.ops);a.i('lw','a2','a3',0);a.nop();a.i('addiu','a2','a2',1)
 miss_store=len(a.ops);a.i('sw','a2','a3',0)
 a.r('sll','a0','a0',5);lib_ptr=len(a.ops);a.i('ori','a1','a3',0);a.r('addu','a1','a1','a0')
 cache_ptr=len(a.ops);a.i('ori','a2','a3',0);a.i('ori','v0','zero',8)
 a.label('copy');a.i('lw','a0','a1',0);a.i('addiu','a1','a1',4);a.i('sw','a0','a2',0)
 a.i('addiu','v0','v0',-1);a.i('bne','zero','v0','copy');a.i('addiu','a2','a2',4)
 a.j('ready');a.nop()
 a.label('hit');hit_load=len(a.ops);a.i('lw','a2','a3',0);a.nop();a.i('addiu','a2','a2',1)
 hit_store=len(a.ops);a.i('sw','a2','a3',0)
 a.label('ready');ready_ptr=len(a.ops);a.i('ori','a2','a3',0);a.j(COMMON);a.i('ori','a3','zero',0)
 code_end=a.pc;owner=code_end;miss=owner+4;hit=owner+8;cache=owner+12;library=cache+32
 assert library+32*len(glyphs)<=END
 for at,value in [(owner_load,owner),(owner_store,owner),(miss_load,miss),(miss_store,miss),
                  (hit_load,hit),(hit_store,hit),(cache_ptr,cache),(ready_ptr,cache),(lib_ptr,library)]:
  op,rt,rs,_=a.ops[at];a.ops[at]=(op,rt,rs,value&65535)
 code=a.words();md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN);md.detail=True
 ins=list(md.disasm(code,START));assert len(ins)==len(a.ops)
 for expected,actual in zip(a.ops,ins):
  name=actual.mnemonic
  assert name==expected[0] or (expected[0]=='beq' and name=='beqz') or (expected[0]=='bne' and name=='bnez'),(expected,name)
  op=expected[0];operands=actual.operands
  def reg(n):return actual.reg_name(operands[n].reg)
  if op in ['ori','andi','addiu','sltiu']:
   assert (reg(0),reg(1),operands[2].imm)==expected[1:]
  elif op=='lui':assert (reg(0),operands[1].imm)==(expected[1],expected[3])
  elif op in ['lw','lbu','sw']:
   assert (reg(0),actual.reg_name(operands[1].mem.base),operands[1].mem.disp)==expected[1:]
  elif op in ['addu','sltu']:assert tuple(reg(i) for i in range(3))==expected[1:]
  elif op=='sll':assert (reg(0),reg(1),operands[2].imm)==expected[1:]
  elif op in ['beq','bne']:
   target=a.labels.get(expected[3],expected[3]);assert operands[-1].imm==target
   if name in ['beqz','bnez']:assert reg(0)==expected[2] and expected[1]=='zero'
   else:assert (reg(0),reg(1))==(expected[2],expected[1])
  elif op=='j':assert operands[0].imm==a.labels.get(expected[1],expected[1])
 payload=code+struct.pack('<III',0xffffffff,0,0)+bytes(32)+b''.join(glyphs)
 payload+=bytes(END-START-len(payload))
 return payload,dict(start=START,end=END,code_end=code_end,owner=owner,misses=miss,hits=hit,cache=cache,library=library,
  instructions=len(ins),listing=[f'{i.address:08X} {i.mnemonic} {i.op_str}' for i in ins])

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
 a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 data,summary=inspect(a.source);old=data['/MAP.LZB;1'];font=ImageFont.truetype(str(a.font),12)
 chars='넋뛴샘샴띠갂';glyphs=[raster(font,c) for c in chars]
 bank=data['/DAT/STAYDAT.BIN;1'][0x37838:0x43838]
 assert all(g not in {bank[i:i+32] for i in range(0,len(bank),32)} for g in glyphs)
 payload,meta=assemble(glyphs)
 # The duplicate high/mid loops differ only in branch destinations by delta.
 md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
 external=[]
 # Decode each aligned word independently; a data word must not terminate the
 # scan and silently hide later external control-flow references.
 for i in (ins for off in range(0,len(old)-3,4) for ins in md.disasm(old[off:off+4],BASE+off)):
  if START<=i.address<END:continue
  if i.mnemonic in ['j','jal'] or i.mnemonic.startswith('b'):
   try:target=int(i.op_str.split(',')[-1].strip(),16)
   except ValueError:continue
   if START<target<END:external.append((hex(i.address),i.mnemonic,i.op_str))
 pointers=[]
 for off in range(0,len(old)-3,4):
  value=struct.unpack_from('<I',old,off)[0]
  if START<value<END and not START<=BASE+off<END:pointers.append((hex(BASE+off),hex(value)))
 assert not external and not pointers,(external,pointers)
 new=bytearray(old);new[START-BASE:END-BASE]=payload
 (a.output/'MAP_original.bin').write_bytes(old);(a.output/'MAP_native.bin').write_bytes(new)
 (a.output/'payload.bin').write_bytes(payload)
 meta.update(characters=chars,escape='F0 00 47 4C index_lo index_hi',external_entry_references=external,external_pointer_candidates=pointers,
  original_map_sha256=hashlib.sha256(old).hexdigest(),modified_map_sha256=hashlib.sha256(new).hexdigest(),
  scope='MAP-only renderer prototype, six resident source glyphs, one-entry 32-byte cache')
 (a.output/'native_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in meta.items() if k not in ['listing','characters']},indent=2))

if __name__=='__main__':main()
