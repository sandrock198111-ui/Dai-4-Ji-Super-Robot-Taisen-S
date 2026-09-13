# Local evidence and reproduction

- Repository: `E:/4robot`.
- Immutable PS1 inputs: `00_original/ps1`; SFC translation references: `00_original/sfc`.
- Current test: `03_output/v001_native_loader/SRW4S_v001_native_loader_test.cue`. BIN stays alongside; audio tracks resolve relatively into `00_original/ps1`.
- Intermediates and evidence: `01_work/experiments/native_loader`. Earlier experiments are adjacent; Bold diagnostic withdrawn.
- Original runtime configurations/states/BIOS: `01_work/vram_test`; static analysis: `01_work/extension_analysis`.
- Complete upstream checkout: `01_work/reference/srw4s-kr-patch`, Einbroch at 978ea84. Translation ledger absent upstream; full translation rebuild requires it.
- Core: `06_tools/mednafen/mednafen_psx_libretro.dll`; xdelta: `06_tools/xdelta/xdelta3.exe`; fonts: `06_tools/galmuri`.
- Set `SRW_TEST_ROOT=E:/4robot/01_work/vram_test` and `SRW_CORE=E:/4robot/06_tools/mednafen/mednafen_psx_libretro.dll`.
- Runner: `python 02_scripts/run_psx.py <cue> <UTF-8 config.json>`. Verified published-path config: `01_work/experiments/native_loader/published_path.local.json`; cold boot without RAM edits or state restoration.
- Upstream imports require `PYTHONPATH=E:/4robot/01_work/reference/srw4s-kr-patch/tools`. MIPS verification also requires Unicorn (local install in `06_tools/python`) and Capstone. Python/Pillow required.
- Build sequence: [native_loader_report.md](native_loader_report.md); use each tool's `--help` for arguments.
- Local BIOS differs from core recommended SHA1. Supported-BIOS, independent emulator and hardware validation remain outstanding.
- Original images, BIOS, fonts, extracted assets, states and output BIN are excluded from Git. Folder README files are tracked. This is not a self-contained fresh-machine package.
