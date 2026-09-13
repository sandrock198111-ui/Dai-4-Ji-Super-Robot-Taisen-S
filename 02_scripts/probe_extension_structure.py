"""Read-only disc inspection for long-message extension feasibility."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from isotool import Disc, walk
from lzb import decompress


def inspect(path):
    disc = Disc(str(path))
    root = disc.sector(16)[156:190]
    entries = []
    walk(disc, struct.unpack_from('<I', root, 2)[0],
         struct.unpack_from('<I', root, 10)[0], '', entries)
    index = {n: (l, s) for n, l, s, k in entries if k == 'FILE'}
    names = ['/MAP.LZB;1', '/BTT/BATTLE.LZB;1', '/BTT/M_BANKB.LZB;1',
             '/DAT/M_BANKS.BIN;1', '/DAT/STAYDAT.BIN;1']
    data = {}
    summary = {}
    for name in names:
        raw = disc.read(*index[name])
        decoded = decompress(raw)[0] if '.LZB;' in name else raw
        data[name] = decoded
        summary[name] = dict(lba=index[name][0], file_bytes=len(raw),
                             decoded_bytes=len(decoded),
                             decoded_sha256=hashlib.sha256(decoded).hexdigest())
    disc.f.close()
    return data, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('original', type=Path)
    ap.add_argument('patched', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    original, old_summary = inspect(args.original)
    patched, summary = inspect(args.patched)
    args.output.mkdir(parents=True, exist_ok=True)
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    ranges = {
        '/MAP.LZB;1': [('fb_dispatch', 0x8011046C, 0x180),
                       ('glyph_rasterizer', 0x80110E8C, 0x6CC),
                       ('text_pixel_buffer_transfer', 0x80111558, 0x190),
                       ('nested_text', 0x801116E8, 0x150),
                       ('message_read', 0x80154080, 0x150)],
        '/BTT/BATTLE.LZB;1': [('token_dispatch', 0x80159B50, 0xC0),
                              ('fc_relative_jump', 0x80159FF0, 0x90),
                              ('message_selector', 0x8015A7B8, 0x50)]}
    lines = []
    for name, regions in ranges.items():
        for label, address, length in regions:
            off = address - 0x80106380
            lines.append(f'\n{name} {label}; patched image')
            for ins in md.disasm(patched[name][off:off + length], address):
                lines.append(f'{ins.address:08X}  {ins.mnemonic:8} {ins.op_str}')
    banks = patched['/DAT/M_BANKS.BIN;1']
    headers = struct.unpack_from('<61I', banks)
    active = sorted(set(h for h in headers if h))
    blocks = [b-a for a, b in zip(active, active[1:] + [len(banks)])]
    report = dict(original=old_summary, patched=summary,
                  mbanks_active_headers=len(active), mbanks_max_physical_block=max(blocks),
                  mbankb_headroom_to_builder_limit=61320-len(patched['/BTT/M_BANKB.LZB;1']),
                  caveat='Builder limit is not independently runtime-qualified free RAM.',
                  runtime_tested=False)
    battle = patched['/BTT/BATTLE.LZB;1']
    table = 0x80163F90 - 0x80106380
    report['battle_fc_handlers'] = {
        str(i): hex(struct.unpack_from('<I', battle, table + 4*i)[0])
        for i in range(16)}
    (args.output/'structure.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (args.output/'consumer_disassembly.txt').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
