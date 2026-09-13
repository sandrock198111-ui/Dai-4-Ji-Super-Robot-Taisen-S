"""One-time path migration for local configs/docs; skips binaries and reference Git."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
OLD='E:/4robot/Dai-4-Ji-Super-Robot-Taisen-S'
pairs=[(OLD+'/03_output','E:/4robot/01_work/experiments'),(OLD,'E:/4robot'),
 ('E:/4robot/vram_test','E:/4robot/01_work/vram_test'),
 ('E:/4robot/extension_analysis','E:/4robot/01_work/extension_analysis'),
 ('E:/4robot/srw4s-kr-patch','E:/4robot/01_work/reference/srw4s-kr-patch'),
 ('E:/4robot/sfc','E:/4robot/00_original/sfc')]
pairs += [('E:/4robot/'+p.name,'E:/4robot/00_original/ps1/'+p.name) for p in (ROOT/'00_original/ps1').glob('*.bin')]
def text(s):
 for a,b in pairs:
  s=s.replace(a,b).replace(a.replace('/','\\'),b.replace('/','\\'))
 return s
def obj(v):
 if isinstance(v,str):return text(v)
 if isinstance(v,list):return [obj(x) for x in v]
 if isinstance(v,dict):return {k:obj(x) for k,x in v.items()}
 return v
changed=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or p.suffix.lower() not in ['.json','.md','.txt','.py','.cue','.cmd']:continue
 rel=p.relative_to(ROOT).as_posix()
 if rel.startswith(('.git/','00_original/','06_tools/','99_backup/','01_work/reference/')):continue
 if p.name in ['layout_migration.json','update_layout_paths.py']:continue
 try:old=p.read_text(encoding='utf-8-sig')
 except UnicodeError:continue
 if p.suffix.lower()=='.json':
  try:data=json.loads(old)
  except ValueError:continue
  updated=obj(data)
  if updated==data:continue
  new=json.dumps(updated,ensure_ascii=False,indent=2)
 else:new=text(old)
 if new!=old:p.write_text(new,encoding='utf-8');changed.append(rel)
(ROOT/'05_docs/layout_path_updates.json').write_text(json.dumps(dict(changed_files=changed),indent=2),encoding='utf-8')
print('Updated path references:',len(changed))
