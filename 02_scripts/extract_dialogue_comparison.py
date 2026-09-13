"""Read-only paired M_BANKS candidates; output stays local, not a translation ledger."""
from pathlib import Path
import json,sys,struct,hashlib
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'01_work/reference/srw4s-kr-patch/tools'))
from isotool import Disc,walk
from text_codec import MB_ARITY,parse_record
w=r/'01_work/translation_comparison';w.mkdir(parents=True,exist_ok=True);data={};fonts={};sources={}
for lang in ['ja','ko']:
 path=next(p for p in (r/'00_original/ps1').glob('*.bin') if p.name.endswith('(Track 1)'+('-patched' if lang=='ko' else '')+'.bin'))
 sources[lang]=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 d=Disc(str(path));root=d.sector(16)[156:190];en=[];walk(d,struct.unpack_from('<I',root,2)[0],struct.unpack_from('<I',root,10)[0],'',en);ix={n:(l,s) for n,l,s,k in en if k=='FILE'}
 data[lang]=d.read(*ix['/DAT/M_BANKS.BIN;1']);fonts[lang]=d.read(*ix['/DAT/STAYDAT.BIN;1']);d.f.close()
 (w/f'mbanks_{lang}.bin').write_bytes(data[lang]);(w/f'stay_{lang}.bin').write_bytes(fonts[lang])
assert sources['ja']['sha256']!=sources['ko']['sha256'], 'Original and translation must be distinct inputs'
m=json.loads((r/'01_work/experiments/font_probe/build_manifest.json').read_text(encoding='utf-8'));cm={int(x['gid'],16):x['character'] for x in m['mapping']}
def toks(d,p):
 s=p
 while p<min(s+1024,len(d)):
  b=d[p]
  if b==255:return parse_record(d[s:p+1],MB_ARITY)
  if b<240:p+=1
  elif b<246:p+=2
  else:
   a=MB_ARITY[b];p+=1+(a(d,p) if callable(a) else a)
 raise ValueError()
rows=[]
for h in range(61):
 tabs={l:struct.unpack_from('<I',d,h*4)[0] for l,d in data.items()}
 if not all(tabs.values()):continue
 for e in range(256):
  rec={}
  try:
   for l,d in data.items():
    p=(tabs[l] if l=='ko' else tabs[l]&0xffff0000)+struct.unpack_from('<H',d,tabs[l]+e*2)[0]
    ts=toks(d,p);rec[l]=dict(offset=p,tokens=[dict(g=t.glyph_id,op=t.opcode,raw=t.raw.hex()) for t in ts])
   tx=''.join(cm.get(t['g'],f"<{t['g']:03x}>") if t['g'] is not None else ('\n' if t['op'] in [246,247] else f"[{t['raw']}]") for t in rec['ko']['tokens'])
   rows.append(dict(h=h,e=e,ko_text=tx,**rec))
  except (ValueError,IndexError,struct.error):pass
(w/'candidate_records.local.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
summary=dict(source_images=sources,paired_token_terminated_slots=len(rows),unique_original_offsets=len({x['ja']['offset'] for x in rows}),scope='Candidate slots, including duplicates and unused records; not dialogue count. Hangul mapping partial. Dynamic names unresolved.')
(w/'extraction_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
