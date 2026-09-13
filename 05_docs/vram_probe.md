# RAM precomposed font replacement probe

2026-09-13. Software mednafen PSX core; paired runs restore the same emulator state and input schedule. The only diagnostic mutation zeros 48KiB at RAM 0x80057838. No new VRAM allocation is introduced.

| Scene | Existing text | New text |
|---|---|---|
| Character settings | Entire VRAM identical after 120 frames | 526 differing pixels |
| Map | Entire VRAM identical after 240 frames | 1417 differing pixels |
| First battle | Entire VRAM identical at frames 1/30/60 | 173 pixels at frame 120; 149 at frame 300 |

Restoring glyphs and redrawing the UI converged to identical VRAM. Captured comparisons preserve portraits, map, robots and effects; visible differences occur in new text. This supports a glyph-to-output-pixels path in the sampled consumers and motivates RAM-side precomposed glyph loading without an additional VRAM atlas.

This is not a dynamic cache implementation or full-game safety proof. Glyph mapping, safe RAM placement, load timing, CD latency, consumer transitions and regression coverage remain. Text capacity and relative jumps are separate problems.

Existing BIOS SHA1 213da1cb149b564c0ccb0b12e62d04df367ac851 differs from expected b05def971d8ec59f346f2d9ac21fb742e3eb6917; the core warned about firmware. Repeat with supported firmware and an independent emulator.

Next experiment: alternate two actual precomposed bitmap sets, checking old text retention, new text correctness and menu return. Compositional font adoption is not the current priority.
