"""Reproduce real bitmap A/B/A tests with existing local diagnostic states."""
import argparse,json,os,subprocess,sys,struct
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw

def vram(path):
    d=path.read_bytes();tag=b'&GPURAM[0][0]';assert d.count(tag)==1
    at=d.index(tag)+len(tag);assert struct.unpack_from('<I',d,at)[0]==1048576
    return d[at+4:at+4+1048576]

def compare(a,b,stem='state'):
    state='state.bin' if stem=='state' else stem+'.state'
    png='last.png' if stem=='state' else stem+'.png'
    x,y=vram(a/state),vram(b/state)
    d=ImageChops.difference(Image.open(a/png).convert('RGB'),Image.open(b/png).convert('RGB'))
    return dict(vram_words=sum(x[i:i+2]!=y[i:i+2] for i in range(0,len(x),2)),
        pixels=sum(p!=(0,0,0) for p in d.get_flattened_data()),bbox=d.getbbox())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,required=True)
    ap.add_argument('--fonts',type=Path,required=True);ap.add_argument('--core',type=Path,required=True)
    a=ap.parse_args();a.evidence=a.evidence.resolve();a.fonts=a.fonts.resolve()
    A=(a.fonts/'font_A.bin').read_bytes();B=(a.fonts/'font_B.bin').read_bytes()
    assert len(A)==len(B)==49152 and A!=B
    runner=Path(__file__).with_name('run_psx.py')
    env=os.environ.copy();env.update(SRW_TEST_ROOT=str(a.evidence),SRW_CORE=str(a.core))
    jobs=[('hold_base','real_hold_B'),('redraw_base','real_redraw_B'),
          ('restore_base2','real_restore_ABA'),('map_transition_base','real_map_B'),
          ('battle_base','real_battle_B')]
    results={}
    for baseline,name in jobs:
        c=json.loads((a.evidence/(baseline+'.json')).read_text());c['output']=str(a.fonts/name)
        c['initial_edits']=[dict(address='0x80057838',before=A.hex(),hex=B.hex())]
        if baseline=='restore_base2':
            c['edits']=[dict(frame=150,writes=[dict(address='0x80057838',before=B.hex(),hex=A.hex())])]
            c['captures']=[120,150,360];c['dumps']=[120,150,360]
        config=a.fonts/(name+'.local.json');config.write_text(json.dumps(c),encoding='utf-8')
        with (a.fonts/(name+'.log')).open('w') as log:
            subprocess.run([sys.executable,str(runner),str(a.evidence/'patched.cue'),str(config)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        if baseline=='battle_base':
            result={str(n):compare(a.evidence/baseline,a.fonts/name,f'f{n:06}') for n in [1,30,60,120,300,600,900]}
            assert all(result[str(n)]['vram_words']==0 for n in [1,30,60])
            assert result['300']['pixels']>0
        else:
            result=compare(a.evidence/baseline,a.fonts/name)
            if baseline in ['hold_base','restore_base2']:assert result['vram_words']==0
            else:assert result['pixels']>0
        results[name]=result;print(name,json.dumps(result),flush=True)
    results['scope']='External emulator RAM A/B/A bitmap replacement, not an in-game loader/cache hook'
    results['bios_caveat']='Inherited diagnostic core BIOS mismatch; independent supported-firmware rerun remains'
    (a.fonts/'runtime_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    rows=[('redraw_base','real_redraw_B','last.png'),('map_transition_base','real_map_B','last.png'),('battle_base','real_battle_B','f000300.png')]
    sheet=Image.new('RGB',(640,810),(24,24,24));draw=ImageDraw.Draw(sheet)
    for row,(base,alt,png) in enumerate(rows):
        draw.text((8,row*270+4),base+' : regular / bold',fill='white')
        for col,p in enumerate([a.evidence/base/png,a.fonts/alt/png]):
            im=Image.open(p).convert('RGB');im.thumbnail((288,240));sheet.paste(im,(32+col*320,row*270+24))
    sheet.save(a.fonts/'real_font_comparison.png')

if __name__=='__main__':main()
