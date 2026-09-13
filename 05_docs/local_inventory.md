# Local evidence and reproduction

- Working repository: E:/4robot/Dai-4-Ji-Super-Robot-Taisen-S
- Original and patched Track 1 images remain externally in E:/4robot, without duplicate copies in 00_original.
- Original test configurations/states: E:/4robot/vram_test. Configurations containing original font hex bytes must not be committed.
- Static analysis: E:/4robot/extension_analysis.
- Reference source: E:/4robot/srw4s-kr-patch; https://github.com/Einbroch/srw4s-kr-patch at 978ea84. Translation ledger absent.
- Set SRW_CORE to your local mednafen_psx_libretro.dll. Set SRW_TEST_ROOT to an isolated test directory containing system/ BIOS and saves/.
- Runner: python 02_scripts/run_psx.py <local.cue> <local-config.json>. Config keys: frames, output, load_state, inputs, captures, dumps, initial_edits, edits. Only process RAM is modified.
- Existing audit: set SRW_TEST_ROOT=E:/4robot/vram_test and SRW_CORE, then python 02_scripts/audit_results.py. Existing local snapshots are required.
- Static probe imports upstream isotool/lzb; add upstream tools to PYTHONPATH and use --help.
- Dependencies: Python, Pillow; capstone for disassembly. Emulator core, BIOS, discs and boot/input configurations are local dependencies, not bundled. This is not yet a complete fresh-machine reproduction package.
