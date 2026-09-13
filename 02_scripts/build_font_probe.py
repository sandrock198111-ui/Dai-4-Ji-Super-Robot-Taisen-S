"""Reconstruct exact Galmuri glyph identities, create a font-only diagnostic disc.

Uses supplied local baseline and upstream read-only ISO reader. Never edits input.
This is a static alternate-font image, not a dynamic cache implementation.
"""
import argparse,hashlib,json,struct,sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

def sha(data):return hashlib.sha256(data).hexdigest()
def raster(font,ch):
    im=Image.new('1',(16,16));d=ImageDraw.Draw(im);d.fontmode='1'
    d.text((0,0),ch,font=font,fill=1)
    return bytes(sum(int(im.getpixel((half*8+x,y))!=0)<<(7-x) for x in range(8))
                 for half in range(2) for y in range(16))

def repair(sec):
    """Mode2 Form1 EDC/ECC. Callers verify source sectors round-trip first."""
    f=[];b=[0]*256;ed=[]
    for i in range(256):
        j=(i<<1)^ (0x11d if i&128 else 0);f.append(j);b[i^j]=i
        x=i
        for _ in range(8):x=(x>>1)^(0xd8018001 if x&1 else 0)
        ed.append(x)
    crc=0
    for v in sec[16:2072]:crc=(crc>>8)^ed[(crc^v)&255]
    struct.pack_into('<I',sec,2072,crc)
    header=sec[12:16];sec[12:16]=bytes(4)
    def ecc(major,minor,mult,inc,dst):
        size=major*minor
        for m in range(major):
            index=(m>>1)*mult+(m&1);a=c=0
            for _ in range(minor):
                t=sec[12+index];index=(index+inc)%size;a^=t;c^=t;a=f[a]
            a=b[f[a]^c];sec[dst+m]=a;sec[dst+m+major]=a^c
    ecc(86,24,2,86,2076);ecc(52,43,86,88,2248)
    sec[12:16]=header

def main():
    ap=argparse.ArgumentParser()
    for name in ['source','upstream','font','alternate','output']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();sys.path.insert(0,str(a.upstream/'tools'))
    from isotool import Disc,walk
    a.output.mkdir(parents=True,exist_ok=True)
    disc=Disc(str(a.source));root=disc.sector(16)[156:190];entries=[]
    walk(disc,struct.unpack_from('<I',root,2)[0],struct.unpack_from('<I',root,10)[0],'',entries)
    index={n:(l,s) for n,l,s,k in entries if k=='FILE'}
    stay=disc.read(*index['/DAT/STAYDAT.BIN;1']);base=stay[0x37838:0x43838]
    assert len(base)==49152
    regular=ImageFont.truetype(str(a.font),12);bold=ImageFont.truetype(str(a.alternate),12)
    shapes={}
    for cp in range(0xac00,0xd7a4):shapes.setdefault(raster(regular,chr(cp)),[]).append(chr(cp))
    alternate=bytearray(base);mapping=[];ambiguous=[]
    for i in range(1536):
        glyph=base[i*32:(i+1)*32];chars=shapes.get(glyph,[])
        if len(chars)==1:
            ch=chars[0];replacement=raster(bold,ch);assert any(replacement)
            alternate[i*32:(i+1)*32]=replacement
            mapping.append(dict(gid=hex(i+0x100),character=ch,changed=replacement!=glyph))
        elif chars:ambiguous.append(dict(gid=hex(i+0x100),characters=chars))
    assert len(mapping)>1000, 'Font version/layout does not reconstruct baseline'
    assert not ambiguous,'Ambiguous glyph identity; refuse substitution'
    (a.output/'font_A.bin').write_bytes(base);(a.output/'font_B.bin').write_bytes(alternate)
    out=a.output/'SRW4S_font_B_test.bin';assert out.resolve()!=a.source.resolve()
    shutil.copyfile(a.source,out)
    changed_sectors=[];changes=[]
    copies=[('/DAT/STAYDAT.BIN;1',0x37838,0x3f838),('/DAT/C_DEMOG.BIN;1',0x41afc,0x4aafc)]
    with out.open('r+b') as target:
        for name,mid,high in copies:
            lba,size=index[name];old=disc.read(lba,size);new=bytearray(old)
            assert old[mid:mid+0x8000]+old[high:high+0x4000]==base
            new[mid:mid+0x8000]=alternate[:0x8000];new[high:high+0x4000]=alternate[0x8000:]
            offsets=[i for i,(x,y) in enumerate(zip(old,new)) if x!=y]
            assert all(mid<=i<mid+0x8000 or high<=i<high+0x4000 for i in offsets)
            changes.append(dict(file=name,changed_payload_bytes=len(offsets)))
            for block in sorted({i//2048 for i in offsets}):
                raw=disc.sector_raw(lba+block);check=bytearray(raw);repair(check)
                assert check==raw, f'Source sector EDC/ECC mismatch {lba+block}'
                sec=bytearray(raw);payload=new[block*2048:(block+1)*2048]
                sec[24:24+len(payload)]=payload;repair(sec)
                target.seek((lba+block)*2352);target.write(sec);changed_sectors.append(lba+block)
    disc.f.close()
    # Independently inspect final image: every changed sector is declared; raw
    # header/subheader preserved, and all user bytes outside glyph spans unchanged.
    src=a.source.read_bytes();dst=out.read_bytes();assert len(src)==len(dst)
    actual=[i for i in range(len(src)//2352) if src[i*2352:(i+1)*2352]!=dst[i*2352:(i+1)*2352]]
    assert actual==sorted(changed_sectors)
    final=Disc(str(out))
    for name,mid,high in copies:
        data=final.read(*index[name]);original=Disc(str(a.source));old=original.read(*index[name]);original.f.close()
        assert data[mid:mid+0x8000]+data[high:high+0x4000]==alternate
        for i,(x,y) in enumerate(zip(data,old)):
            if x!=y:assert mid<=i<mid+0x8000 or high<=i<high+0x4000
    final.f.close()
    for lba in actual:
        x=src[lba*2352:(lba+1)*2352];y=dst[lba*2352:(lba+1)*2352]
        assert x[:24]==y[:24];check=bytearray(y);repair(check);assert check==y
    report=dict(kind='static alternate-font diagnostic; not dynamic caching',
        source_sha256=sha(src),output_sha256=sha(dst),font_sha256=sha(a.font.read_bytes()),
        alternate_sha256=sha(a.alternate.read_bytes()),mapped_glyphs=len(mapping),
        changed_glyphs=sum(m['changed'] for m in mapping),unchanged_slots=1536-len(mapping),
        changes=changes,changed_sectors=actual,source_unchanged=sha(a.source.read_bytes())==sha(src),mapping=mapping)
    (a.output/'build_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='mapping'},indent=2))

if __name__=='__main__':main()
