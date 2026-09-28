# UNO Pro Advanced v0.9.6-beta — integration report

Release naming correction: the integration was initially committed locally under the unapproved name `0.10.0-alpha` in commit `2a63c2684c89881003bdd015cc24a58dbde11e95`. The user approved continuation as `0.9.6-beta`. That old local archive is superseded; do not publish it. Functional behavior and PARTIAL/UNKNOWN statuses are unchanged by this correction.

Date: 2026-09-15. Branch: main. Worktree: `D:\UNO\project_unified`.
Starting main: `51906bc1a40a636441c98f10794113d696ffc180`, clean working tree.
Integrated source: `e2b0a977d194fdf28e40eaac73b1eaae8de525b0` (Live Creator v0.6-alpha).
Canonical v0.9.5-beta ZIP app.py matches starting main after CRLF normalization. REFERENCE.zip was not used as base.
Integration uses a non-fast-forward merge, preserving both histories and the Live-Creator worktree's existing changes.

## 1. Integration / Live Creator

IMPLEMENTED: LIVE embedded in the main window; no CREATOR/LIVE switch, legacy SONG controls not displayed. One grid of 64 independent songs, one 64-slot timeline in two rows, reference-only presets, existing menus/clipboard/markers/loop/pulse preserved.
LENGTH is independent of occupied step count and preset Sequence Length. Default 64; allowed 1–64. Slots after it are dimmed, no data deletion. Timing and block statistics stop at the earlier of occupied content or LENGTH; selected start outside LENGTH restarts at beginning. Loop range clips to the playback snapshot end. Editor changes affect the next snapshot, not currently playing song.
Blocks use smooth rounded canvas polygons with a 4px corner control radius; selection outline uses the same shape. Pads remain dark in Light theme.
Service state: `%LOCALAPPDATA%\UnoLive\state\live_creator_state.json`, reading previous state versions. Existing unknown EMPTY duration policy remains: no invented duration/playback for gaps.

## 2. Sequencer / Dupl

IMPLEMENTED / SOFTWARE TEST PASS for 8→16, 12→24, 16→32, 32→64, no partial copying, deep-copy notes/control fields and automation values/fine values/raw CC captures. Result above 64 disabled. Existing Fill method is unchanged.

### Mini-manual

**Dupl — Duplicates the current sequence into the following steps, including Step Automation. Sequence Length is doubled. Available when the resulting length does not exceed 64 steps.**

Fill all 64 steps with sequences.

Safety limitation: native entries whose step/value mapping is unknown cannot be duplicated honestly. Dupl is disabled for such native payloads (PARTIAL); raw source remains intact. This is not claimed as native automation writer support.

## 3. Automation Reader / UI

IMPLEMENTED: `AUTOMATION [parameter]`, existing Modulation Matrix multi-column picker pattern; no banks/pages. Graph geometry remains y=820, height=128, same step layout.
22 held-Step targets: CUTOFF 1/2, RESONANCE 1/2, LEVEL 1/2/3, TUNE 1/2/3, LFO 1/2, WAVE 1/2/3, SPACING, ENV AM 1/2, DRIVE AMOUNT, MODULATION AMOUNT, DELAY AMOUNT, REVERB AMOUNT. FM/KEYTRACKING are not selectable.
Shared metadata contains polarity, min/max, units, labels and evidence status. Cutoff 0–512, resonance 0–127, level/effect amounts per documented ranges, spacing/env ±64. Tune hybrid ±99 cents / ±24 semitones is PARTIAL; free-Hz/sync interpolation and normalized Wave mapping are not invented. Unknown scales show UNKNOWN. PARTIAL interpolation is not editable as a fabricated linear range.
New empty lines contain None, not fake zeros/center. Existing legacy 7-bit values are retained but are not reinterpreted as device-unit graph samples. Existing CC recording goes to separate raw cc_values. Only legacy/captured raw CC samples use existing send mappings; UI units never become guessed MIDI bytes.
Native reader: `data[494]` byte length, payload starts 496, tested pairs of two bytes, count=length/2. Validates even length/bounds, preserves byte495 and all raw bytes; no fixed MAX=17. Known isolated saved pairs remain raw, not parameter IDs. Header shows native entry count and mapping PARTIAL rather than fabricated graph points.

### Supplied capture validation (read-only)

| File | Payload bytes | Entries |
|---|---:|---:|
| REF2 | 0 | 0 |
| AUTO_L4 | 2 | 1 |
| AUTO_L5 | 2 | 1 |
| AUTO_L6 | 4 | 2 |
| AUTO_L | 28 | 14 |
| AUTO_L2 | 34 | 17 |

Source folder: `D:\UNO\materials\test`. Pairs 2901, 580e, 580e08c3 matched. Full raw source and container survive load. 12 LEN files confirmed lengths 1,2,4,8,9,10,16,17,32,33,48,64. This is SOFTWARE validation of supplied real captures, not a new HARDWARE PASS.
Sequence Length: `value=data[207] | data[208]<<7`; `length=(value+1)//8`; inverse `length*8-1`, only bytes207/208 changed by standalone helper. No last-active-step inference. Live timing uses confirmed 1/16 steps: beats=length/4.

## 4. Theme / toolbar / storage

IMPLEMENTED: central semantic tokens in ui_theme.py; Light panels/text, Orange↔Blue accent swap, invariant green PLAY/red REC. Live fill colors and dark empty pads preserved; NAME remains song-colored. Settings gear tooltip Settings, Theme icon tooltip Theme directly before scale, keyboard retained. User setting `theme` persists.
All new service writes use `%LOCALAPPDATA%\UnoLive`. Legacy settings/metadata may be read from the former Documents folder without writing there. No generated songs folder at startup. User presets are not migrated/copied. Tag data/filters remain; row circles removed.

## 5. Verification

Version-correction pass: 57 unittest PASS, compile/import PASS, runtime diff is strictly the version string, shared docs mirrors match. GUI checks below passed for the integration before renaming, but could not be repeated for v0.9.6-beta: the former Tcl/Tk test folder is absent and access to installed Python was denied by approval infrastructure. Current beta launch / GUI recheck is therefore UNVERIFIED, not a newly claimed PASS. CRC/manifest checks are performed on the rebuilt beta archive.

- 57 current unittest checks: Live regression plus integration model/storage/safety checks.
- Real Tk software GUI: all pages in both themes, embedded Live, LENGTH/inactive slots/radius, 64 pads, selection isolation, picker, Dupl, no MIDI sends.
- Standalone Live GUI regression: menus, palette, clipboard keys, markers, shapes and three window sizes.
- Supplied capture reader validation: 6 automation files and 12 lengths, all read-only.
- Compile/import; git diff --check; byte-identical MIDI/protocol modules; AST-identical STORE and Fill methods.
- Historical `Docs/test_beta.py` is not an applicable release gate: 12/15 errors reproduced on starting main (removed dirty/working-file API and BOM assumption). Two additional old SONG tests assume the superseded .unosong UI/mock-only Tk root; replacement real Tk integration tests cover LIVE. Historical files left unchanged, no false claim of passing them.
- Direct visual computer-use was rejected by tool approval infrastructure (incompatible compaction checkpoint); visible installed-Python launch was denied access. No workaround used. Manual final visual acceptance is UNVERIFIED, software rendering checks are separate.

## 6. PARTIAL / UNKNOWN / HARDWARE UNVERIFIED

Native two-byte entry parameter/value/step semantics and writer PARTIAL; exact maximum entries and byte495 purpose UNKNOWN. Native events cannot yet become trustworthy graph points or be duplicated. Legacy raw CC-to-device-unit graph conversion unverified; preserve raw. Tune hybrid, Wave normalization and LFO mode-aware editing PARTIAL. No new automation encoders.
Marker collision rejects edit atomically instead of joining labels. EMPTY musical duration unknown. Live Creator playback remains software-only, no sound/MIDI/preset sends/controller/hardware SONG writes. Real hardware was not exercised. STORE/0x28 and unknown SEQ ON/OFF remain untouched.

## 7. Build

Version: 0.9.6-beta. Date: 2026-09-15.
Format: source standalone folder + ZIP, Python 3.12+ / Tkinter / Pillow; not an autonomous EXE.
Path: `D:\UNO\project_unified\builds\UNO_Pro_Advanced_v0.9.6-beta.zip`.
Source commit: see `BUILD_COMMIT` inside release; manifest hashes included. Build is created after commit and rejects overwriting historical releases. The previous integration launch used packaged main with mocked MIDI and isolated settings. Repeating launch on the corrected beta is blocked by unavailable Tcl/Tk/access; manual launch remains to be checked. No hardware pass implied.
