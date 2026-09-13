"""Place only runnable deliverables in 03_output; verify copied BIN hash."""
from pathlib import Path
import json,hashlib,shutil

ROOT=Path(__file__).resolve().parents[1]
work=ROOT/'01_work/experiments/native_loader'
out=ROOT/'03_output/v001_native_loader';out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
info=json.loads((work/'disc_verification.json').read_text(encoding='utf-8'))
assert sha(work/'SRW4S_native_loader_demo.bin')==info['output_sha256']
for src,dst in [('SRW4S_native_loader_demo.bin','SRW4S_v001_native_loader_test.bin'),
                ('SRW4S_native_loader_from_v099W.xdelta','SRW4S_v001_from_v099W.xdelta'),
                ('LICENSE_Galmuri.txt','LICENSE_Galmuri.txt')]:
 if not (out/dst).exists() or sha(work/src)!=sha(out/dst):
  shutil.copy2(work/src,out/dst)
assert sha(out/'SRW4S_v001_native_loader_test.bin')==info['output_sha256']
tracks=ROOT/'00_original/ps1'
track2=next(tracks.glob('*Track 2*.bin'));track3=next(tracks.glob('*Track 3*.bin'))
cue='FILE "SRW4S_v001_native_loader_test.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
for n,p,index in [(2,track2,'00:02:00'),(3,track3,'03:00:00')]:
 name=f'SRW4S_Track{n:02}.bin'
 shutil.copy2(p,out/name)
 assert sha(p)==sha(out/name)
 cue+=f'FILE "{name}" BINARY\n  TRACK {n:02} AUDIO\n    INDEX 00 00:00:00\n    INDEX 01 {index}\n'
(out/'SRW4S_v001_native_loader_test.cue').write_text(cue,encoding='utf-8')
shutil.copy2(work/'coldboot/last.png',out/'preview.png')
info['coldboot']=json.loads((work/'coldboot_verification.json').read_text(encoding='utf-8'))
(out/'BUILD_INFO.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
print(out)
