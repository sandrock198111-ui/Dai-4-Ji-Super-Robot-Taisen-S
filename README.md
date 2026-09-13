# Dai-4-Ji Super Robot Taisen S Korean patch research

Japan Rev 1 / Einbroch v0.99W continuation. Preserve the existing 1bpp precomposed Regular typeface; do not shorten translations to fit glyph capacity. SFC is a translation reference.

Repository root: `E:/4robot`.

| Directory | Purpose |
|---|---|
| 00_original | Immutable PS1 inputs and SFC references |
| 01_work | Upstream checkout, analysis and experiment intermediates |
| 02_scripts | Build and verification scripts |
| 03_output | Executable test builds |
| 04_screenshots | Screen evidence |
| 05_docs | Reports and project records |
| 06_tools | Local tools and fonts |
| 99_backup | Backups |

Current local test: `03_output/v001_native_loader/SRW4S_v001_native_loader_test.cue`.
BIN, xdelta and Korean instructions are alongside. This implements six resident glyphs and a single RAM cache entry in the MAP renderer. Bulk font supply, battle integration and long-text expansion remain outstanding.

[Native loader report](05_docs/native_loader_report.md) / [Local inventory](05_docs/local_inventory.md).

Read AGENTS.md and the designated starting documents before working. Folder README files are tracked; disc images, BIOS, extracted data and output BIN files remain local.
