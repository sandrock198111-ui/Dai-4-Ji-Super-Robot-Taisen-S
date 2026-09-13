"""Read-only IPS/ROM identity and header survey; does not infer script format."""
import argparse, hashlib, json
from pathlib import Path

def digest(b): return hashlib.sha256(b).hexdigest()

def apply_ips(source, patch):
    assert patch[:5] == b'PATCH'
    out = bytearray(source); pos = 5; records = []
    while patch[pos:pos+3] != b'EOF':
        at = int.from_bytes(patch[pos:pos+3], 'big')
        n = int.from_bytes(patch[pos+3:pos+5], 'big'); pos += 5
        if n:
            data = patch[pos:pos+n]; assert len(data) == n; pos += n
        else:
            n = int.from_bytes(patch[pos:pos+2], 'big')
            data = bytes([patch[pos+2]]) * n; pos += 3
        if len(out) < at+n: out.extend(bytes(at+n-len(out)))
        out[at:at+n] = data; records.append((at,n))
    pos += 3
    if len(patch)-pos == 3:
        size = int.from_bytes(patch[pos:], 'big')
        out = out[:size] + bytes(max(0, size-len(out)))
    else: assert pos == len(patch)
    return bytes(out), records

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('folder',type=Path); ap.add_argument('output',type=Path)
    args=ap.parse_args(); files={p.name:p.read_bytes() for p in args.folder.iterdir() if p.is_file()}
    original=next(v for k,v in files.items() if '(Japan)' in k)
    korean=next(v for k,v in files.items() if k.endswith('.sfc') and '(Japan)' not in k)
    patch=next(v for k,v in files.items() if k.endswith('.ips'))
    rebuilt,records=apply_ips(original,patch)
    report=dict(files={k:dict(bytes=len(v),sha256=digest(v)) for k,v in files.items()},
        ips_records=len(records), ips_matches_supplied_korean=rebuilt==korean,
        original_bytes=len(original),korean_bytes=len(korean),
        changed_original_bytes=sum(a!=b for a,b in zip(original,korean)),
        added_bytes=len(korean)-len(original),
        headers={k:[dict(offset=hex(o),title=v[o:o+21].decode('ascii','replace'),
            map_mode=hex(v[o+21]),rom_size_field=v[o+23]) for o in [0x7fc0,0xffc0]]
            for k,v in files.items() if k.endswith('.sfc')},
        script_format_verified=False,font_format_verified=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=='__main__':main()
