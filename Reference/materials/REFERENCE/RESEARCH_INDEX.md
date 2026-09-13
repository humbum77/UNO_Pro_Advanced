# RESEARCH_INDEX.md

Start here after opening the project:
1. `PROJECT_STATE.md` — authoritative current release/state and limitations.
2. `FIXED_CHANGES.md` — cumulative mandatory/frozen decisions.
3. `UNO_PROJECT_TASKS.md` — master backlog/status.
4. `HARDWARE_TEST_RESULTS.md` — real UNO tests, including 2026-09-08 `test3` preset synchronization.
5. `SYSEX_PROTOCOL.md` — confirmed/unknown SysEx, including `0x24`, `0x32`, `0x37`.
6. `MIDI_REFERENCE.md` — official CC/Program Change and frozen FX values.
7. `GUI_SPEC.md` — frozen UI/Library behavior.
8. `FILE_FORMATS_PATHS.md` — storage paths and file formats.
9. `PRESET_FLASH_FORMAT.md` / `UPDATER_DFU_RESEARCH.md` — lower-level research.
10. `UNO_TEST_DATA_ALL.md` — raw research archive.
11. `BUILD_RULES.md` — explicit-build-only and cumulative validation rules.


## 2026-09-09 state-map research
- `STATE_0x37_MAP.md` — current interpretation, safety rules and sequential-scan caveat.
- `STATE_0x37_PARAMETER_MAP.csv` — compact CC/GUI-key -> offsets/masks/unique-state count map used to audit v1.52.
- Runtime `state_decoder_map.json` — compact exact-observed signatures used by v1.52; generated from the 11,136-point real-hardware sweep.
- External/raw research artifacts are intentionally not duplicated into Docs when large; the project keeps the compact map plus conclusions.


## 2026-09-10 v1.58 integration references
1. Runtime `unosyp_state_decoder.py` — read-only `.unosyp` ↔ 260-byte raw-state ↔ synthetic `0x37` bridge, ARP/Voice/Matrix extended fields.
2. Runtime `unosyp_seq_decoder.py` — confirmed 1081-byte 64-step read-only sequence decoder; 1084-byte variant intentionally unsupported.
3. `VALIDATION_v158_RU.md` — pre-package software/headless validation and explicit hardware limitations.
4. `test_v158_regression.py` + `test2.unosyp`..`test5.unosyp` — reproducible local regression fixtures.
