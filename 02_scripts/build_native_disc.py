"""Make the native-loader scene demo from a verified baseline; preserve fonts."""
import argparse,json,struct,shutil,hashlib,sys
from pathlib import Path
from build_font_probe import repair

def main():
 ap=argparse.ArgumentParser()
 for k in ['source','upstream','output']:ap.add_argument('--'+k,type=Path,required=True)
 ap.add_argument('--baseline-roundtrip',action='store_true',help='Run foundational four-file compression checks')
 a=ap.parse_args();p=a.output.resolve();sys.path.insert(0,str(a.upstream/'tools'))
 from isotool import Disc,walk
 from lzb import decompress
 from lzb_encode import compress
 d=Disc(str(a.source));root=d.sector(16)[156:190];entries=[]
 walk(d,struct.unpack_from('<I',root,2)[0],struct.unpack_from('<I',root,10)[0],'',entries)
 idx={n:(l,s) for n,l,s,k in entries if k=='FILE'}
 roundtrips=[]
 for name in (['/MAP.LZB;1','/MOVIE.LZB;1','/BTT/BATTLE.LZB;1','/BTT/M_BANKB.LZB;1'] if a.baseline_roundtrip else []):
  raw=d.read(*idx[name]);plain=decompress(raw)[0];packed=compress(plain);assert decompress(packed)[0]==plain
  roundtrips.append(dict(file=name,original=len(raw),recompressed=len(packed),decoded=len(plain)))
  (p/'baseline_roundtrips.json').write_text(json.dumps(roundtrips,indent=2))
  print('roundtrip',name,len(packed),flush=True)
 raw=d.read(*idx['/MAP.LZB;1']);plain=decompress(raw)[0];assert plain==(p/'MAP_original.bin').read_bytes()
 new=(p/'MAP_native.bin').read_bytes();packed=compress(new);assert decompress(packed)[0]==new
 (p/'MAP_native.lzb').write_bytes(packed)
 assert len(packed)<=(len(raw)+2047)//2048*2048,'No new sectors allowed'
 changes={'/MAP.LZB;1':packed}
 # Root-directory file length changes only; LBA and allocated sector count stay.
 root_lba=struct.unpack_from('<I',root,2)[0];root_size=struct.unpack_from('<I',root,10)[0]
 directory=bytearray(d.read(root_lba,root_size));pos=0;found=[]
 while pos<len(directory):
  size=directory[pos]
  if not size:pos=(pos//2048+1)*2048;continue
  name=bytes(directory[pos+33:pos+33+directory[pos+32]])
  if name==b'MAP.LZB;1':found.append(pos)
  pos+=size
 assert len(found)==1;entry=found[0]
 assert struct.unpack_from('<I',directory,entry+10)[0]==len(raw)
 struct.pack_into('<I',directory,entry+10,len(packed));struct.pack_into('>I',directory,entry+14,len(packed))
 changes['@ROOT']=bytes(directory);idx['@ROOT']=(root_lba,root_size)
 stay=d.read(*idx['/DAT/STAYDAT.BIN;1']);needle=bytes.fromhex('f56ef35af3cbf574f4dff29a');assert stay.count(needle)==1
 at=stay.index(needle);mod=bytearray(stay);mod[at:at+12]=bytes.fromhex('f000474c0000f000474c0100')
 changes['/DAT/STAYDAT.BIN;1']=bytes(mod)
 assert mod[0x36838:0x43838]==stay[0x36838:0x43838]
 out=p/'SRW4S_native_loader_demo.bin';assert out.resolve()!=a.source.resolve();shutil.copyfile(a.source,out);sectors=[]
 with out.open('r+b') as dest:
  for name,data in changes.items():
   lba,size=idx[name];old=d.read(lba,len(data))
   assert len(data)<=(size+2047)//2048*2048
   blocks=sorted({i//2048 for i,(x,y) in enumerate(zip(old,data)) if x!=y})
   for block in blocks:
    before=d.sector_raw(lba+block);check=bytearray(before);repair(check);assert bytes(check)==before
    sector=bytearray(before);payload=data[block*2048:(block+1)*2048];sector[24:24+len(payload)]=payload;repair(sector)
    dest.seek((lba+block)*2352);dest.write(sector);sectors.append(lba+block)
 d.f.close()
 # Independent final-image readback and exact sector whitelist.
 original=a.source.read_bytes();built=out.read_bytes();assert len(original)==len(built)
 actual=[i for i in range(len(built)//2352) if original[i*2352:(i+1)*2352]!=built[i*2352:(i+1)*2352]]
 assert actual==sorted(sectors)
 final=Disc(str(out))
 for name,expected in changes.items():assert final.read(idx[name][0],len(expected))==expected
 final_entries=[];walk(final,root_lba,root_size,'',final_entries)
 final_idx={n:(l,s) for n,l,s,k in final_entries if k=='FILE'}
 assert final_idx['/MAP.LZB;1']==(idx['/MAP.LZB;1'][0],len(packed))
 assert all(final_idx[n]==v for n,v in idx.items() if n not in ['@ROOT','/MAP.LZB;1'])
 assert decompress(final.read(*final_idx['/MAP.LZB;1']))[0]==new
 final.f.close()
 for block in actual:
  b=built[block*2352:(block+1)*2352];assert b[:24]==original[block*2352:block*2352+24]
  c=bytearray(b);repair(c);assert c==b
 report=dict(source_sha256=hashlib.sha256(original).hexdigest(),output_sha256=hashlib.sha256(built).hexdigest(),
  source_unchanged=hashlib.sha256(a.source.read_bytes()).digest()==hashlib.sha256(original).digest(),
  baseline_lzb_roundtrips=roundtrips,new_map_compressed=len(packed),previous_map_file_size=len(raw),
  root_size_field_changed=True,additional_sectors=0,
  staydat_demo_literal_offset=hex(at),demo_literal_bytes=12,changed_sectors=actual,
  original_font_banks_unchanged=True,scope='Scene demo: MAP-only native escape, six source glyphs, one-entry cache')
 (p/'disc_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
