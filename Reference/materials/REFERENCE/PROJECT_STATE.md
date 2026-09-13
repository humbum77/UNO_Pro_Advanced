# PROJECT_STATE.md

Current test release: UNO Pro Advanced v1.58 test build candidate (cumulative from accepted v1.57 plus post-v1.57 protocol research).
Date: 2026-09-10.

## Current focus
Hardware preset -> complete SYNTH GUI restoration from the confirmed 309-byte `0x37` current-state reply. v1.52 adds an exact-observed LUT decoder built from the real-hardware Full State Mapper sweep.

## Hardware-confirmed foundation
- v1.51 hardware preset names via `0x24` work on real UNO.
- Preset number synchronization works both directions.
- Official/test3 sequence remains Program Change + `0x32` -> `0x37` -> `0x24`.
- Full State Mapper v1.3 HOTFIX completed 87 known preset CC controllers × all 128 CC points, retaining full 309-byte states.
- Differential analysis found observed signatures for 83/87 scanned CCs. Shared serialized bytes use disjoint bit masks in this sweep; no pair of mapped controls overlaps the same observed bit.

## v1.52 behavior
On each 309-byte `0x37` response the editor decodes all exact signatures known from the hardware sweep and updates GUI state without sending those values back to the synth. Enum/toggle fields use observed state ordinals; continuous fields use the observed CC/native value mapping. Unseen signatures are deliberately skipped rather than guessed. The status line reports applied/unseen/unlabeled counts.

## Important limitations
This is still a hardware-sync TEST release, not a declaration that every bit of all 309 bytes is semantically decoded. The sweep was sequential, so some fields are context-dependent (notably Delay/Reverb modes); four scanned CCs produced no state change in that scan context: CC7, CC110, CC111, CC112. GUI controls without a confirmed state/CC mapping also remain outside the decoder.

## Frozen rules
See `FIXED_CHANGES.md`. STORE remains locked until `0x28` is safely decoded. Frozen FX hardware mappings and existing preset-number/name behavior must not regress.


## v1.53 test focus
GUI visibility test for MODULATION third-level states. CHORUS now uses horizontal SYNTH1/SYNTH2/STRINGS buttons and PHASER uses COLOR1/COLOR2, preserving the former dropdown ordinal values 1:1. LOCAL Library now presents first-level folders only and recursively flattens nested `.unosyp` files. Envelope editing is point-only with hover-visible points, plus a separate live visual position marker. Hardware semantics are not guessed; PHASER state remains a hardware validation target.


## UNO Pro Advanced build delta
Library architecture is now LOCAL-left / UNO-or-open-folder-right, with ALL recursive local view, compact panel-local tools, local-only favorite/color metadata, and alphabetic column views. The envelope live marker is white/small and clears after Release. Confirmed third-level MOD UI sends CC98 0/42/84 for Chorus and CC96 0/127 for Phaser Color. STORE remains locked.


## 2026-09-10 Library refinement
The left Library workspace is widened, the right target panel is compact, and the gap is fixed at 10 px. LOCAL labeling is removed from the left toolbar; Add Folder stays left while favorite/color filters are right-aligned. UNO is left-aligned in the right toolbar with Receive/Send right-aligned. Library fonts are +2 pt. Short left-click selects and opens the relevant preset/folder menu; moving beyond the drag threshold performs drag/drop. LOCAL-to-UNO cannot bypass the permanent STORE lock.

## v1.54 — LOCAL preview + Library interaction polish (2026-09-10)
- P0 IMPLEMENTED: selecting a LOCAL JSON `.unosyp` applies its saved `values` / `choice` / `toggle` / filter-link state to the editor and redraws the GUI.
- P0 IMPLEMENTED: LOCAL preview sends only existing confirmed live CC mappings/current-buffer controls; it does not issue Program Change and does not call STORE/`0x28`.
- FROZEN: UNO/HARDWARE Library selection behavior is unchanged.
- IMPLEMENTED: preset left click selects + previews; preset context menu is right-click only.
- IMPLEMENTED: preset context menu is dark and has Favorite star + seven smooth circular color tags in one row, followed by Rename/Copy/Cut/Paste/Delete. `Load` and `Tags` submenu are removed.
- IMPLEMENTED: preset row icons are removed; names and metadata marks remain.
- IMPLEMENTED: Add Folder toolbar icon is removed; New folder remains in folder context menu with inline naming.
- IMPLEMENTED: right toolbar label is `Uno`, placed immediately before Receive/Send at the right edge.
- IMPLEMENTED: main preset selector shows only the LOCAL preset name (no folder prefix); hardware source menu label is exactly `UnoSynth`.
- IMPLEMENTED: topbar READ button removed.
- LIMITATION: official opaque/binary IK `.unosyp` semantic preview remains locked until that binary format is decoded safely; v1.54 preview applies to editor-native JSON presets.


## v1.55 — LOCAL binary preview test (2026-09-10)
- TEST/NOT YET HARDWARE-CONFIRMED: official UNO Synth Pro binary `.unosyp` matching header `25 01 00 00` and expected payload length may be previewed using externally documented current-buffer SysEx `0x36`; no Program Change, STORE or `0x28` is sent.
- After `0x36`, editor requests current state `0x37` so confirmed decoder fields can rebuild GUI from the UNO response.
- SAFETY: malformed/unexpected binary files are rejected rather than transmitted. This `0x36` path must remain TEST until reproduced on the user's real UNO.
- UI: preset context menu Favorite star is always yellow; seven smaller anti-aliased circular tags are shown directly in one row. Library tag dots use anti-aliased rendering.


## v1.57 cumulative integration — 2026-09-10
1. Baseline is the physical v1.55 archive. v1.56 is treated as an unsuccessful test build and is not the cumulative baseline.
2. LOCAL binary `.unosyp` sequence decode is integrated into the editor model: 4 pages × 16 steps, 10-byte step records, up to 3 notes per step, per-note velocity/extra and raw control preserved. This is read-only and does not unlock STORE.
3. Settings uses Preview=ON as the first-run default and a dirty-state APPLY workflow; there is no SAVE SETTINGS button.
4. Library cumulative fixed UI is applied: main selector has no source/path prefix, source label `UnoSynth`, Tags submenu is star + 7 circles, explicit tag gap, narrower tree / wider LOCAL workspace, draggable horizontal scroll, Shift-wheel horizontal scroll, drag filename ghost + target feedback, and one-step UP/DOWN metadata ordering.
5. SONG has an in-page recursive LOCAL folder tree and preset contents list for slot assignment, without requiring Library navigation.
6. Filter ENV visualization maps bipolar +64 to the full positive cutoff span. Envelope marker starts at Attack on Note On, traverses Attack/Decay, holds at Sustain entry, and traverses Release from the actual current level after Note Off.
7. Post-v1.57 research adds read-side Voice Mode candidate (2-bit 0/1/2 = MONO/LEGATO/PARA, high-confidence but not hardware-differential-confirmed) and confirmed Mod Matrix Source/Destination packed-state decoding. Matrix Fade In raw 10-bit field is located but its semantic scale is still intentionally unmapped.
8. STORE/0x28 remains locked. 0x36 remains TEST/NOT HARDWARE-CONFIRMED.


## v1.58 test-build integration — 2026-09-10
1. `.unosyp` bytes 0..296 are decoded read-only into the same 260-byte synth/current-state representation used by `0x37`; a synthetic 309-byte frame is passed through the exact hardware-observed LUT.
2. Confirmed 1081-byte `.unosyp` sequence variant remains 4 pages × 16 steps × 10-byte records. The 1084-byte test5 variant remains state-only; no sequence semantics are attempted.
3. LOCAL binary load applies synth-state + extended ARP/Matrix/Voice read-side fields without MIDI echo. Sequence origin is tracked explicitly in the GUI.
4. Hardware preset selection and `0x37` receive are marked `HARDWARE_STATE_ONLY`; stale LOCAL sequence data is cleared when switching to a different hardware preset. The sequencer page explicitly says that 64 hardware steps were not read.
5. ARP confirmed live paths in this build: `0x3E` receive for Direction/Range/Pattern and `0x3C 00 02` send for the 16-step Pattern. Range writes native values 1..4. ARP ON/OFF remains unmapped and no guessed command is sent.
6. Mod Matrix raw-state read formula: Destination bits 5..10, Fade raw bits 11..20, Amount raw bits 21..28, Source = current bits 29..31 + next chunk bits 0..4. Factory slot59 cross-check reproduces routes `(27,1,14)`, `(41,2,31)`, `(32,17,10)`, `(29,0,18)`.
7. Matrix Fade In raw 10-bit field is preserved for research only and is NOT applied to GUI `MFADE` until the display/time scale is proven.
8. `0x28` remains locked. Runtime contains no `0x28` SysEx constructor. `0x36` remains experimental/current-buffer preview only and is not hardware-confirmed.
9. Software/headless regression suite is in `Docs/test_v158_regression.py`; fixtures `test2`–`test5` are included under Docs for reproducibility.
10. Hardware validation is still required for real UNO behavior. Software/headless PASS must not be reported as hardware PASS.


## Fixed next-work GUI target — ADSR visualization (2026-09-11)
1. User-approved visual behavior is now fixed for both FILTER ENV and AMP ENV.
2. A/D/R should become visibly responsive at approximately 20 ms equivalent rather than the current approximately 75 ms visual threshold.
3. Sustain should form a horizontal S→R segment from approximately 3% upward, with line height following S.
4. Implementation must use nonlinear/log-like visual time mapping and must not change MIDI/raw ADSR values or protocol behavior.
5. Status: SPECIFIED / NOT YET IMPLEMENTED in v1.58.

## Working changes for next build v1.59 — implementation pass started 2026-09-11
1. ADSR graph geometry now has a nonlinear graph-only A/D/R mapping, with short-time response expanded visually; MIDI/raw ADSR values are unchanged.
2. ADSR editor interaction now follows the fixed model: AD point horizontal only; DS point horizontal + vertical; SR sustain segment vertical; R point horizontal only.
3. Sequencer Piano Roll now selects an existing note with one click, deletes an existing note on double-click, and visually extends each note according to its stored `length` value.
4. Sequencer CLEAR now uses an in-theme confirmation window with `ДА` / `НЕТ`.
5. LFO1/LFO2 Fade In defaults are now explicitly `OFF` (`0`) in editor defaults.
6. Matrix dropdown wheel focus is fixed in the working source: while a dropdown is open, wheel input scrolls only that dropdown and no longer scrolls the Matrix underneath it.
7. LIBRARY working source: hardware presets are arranged in horizontally scrollable columns; wheel scrolling works over both LOCAL preset columns and HARDWARE columns; long LOCAL names are clipped with ellipsis; left-click folder release no longer opens the folder context menu.
8. SONG working source: preset browser is now a simple expandable tree. A single click on a folder opens/closes it; keyboard arrow navigation remains available.
9. Session state working source: selected LOCAL/HARDWARE preset is saved on exit and restored on startup without transmitting Program Change or preview SysEx merely because of restore.
10. Existing filter visualization already consumes supported LFO Matrix modulation and animates the filter curve when an LFO is routed to Filter 1/2 Cutoff with nonzero amount; this path remains preserved and is covered as a software visualization behavior, not hardware protocol validation.
11. ARP RATE is NOT a hardware parameter on UNO Synth Pro. The erroneous editor-only `ARP_RATE` control/value has been removed from the v1.59 working source. Do not assign CC/SysEx or reintroduce it as a hardware control.
12. Status: WORKING SOURCE ONLY. No v1.59 ZIP/build has been created yet.


## Matrix Fade In clarification — 2026-09-11
1. User confirms Matrix Fade In works in current use. Preserve its existing behavior in v1.59; it is not an active UI/function defect.
2. Separate protocol-research caveat remains: the packed-state 10-bit `fade_raw` read-side semantic scale has not been independently decoded, so do not replace the working behavior with a guessed state mapping.

## 2026-09-11 v1.59 protocol updates
1. Voice Mode receive confirmed: raw byte 175 bits 5-6 = MONO/LEGATO/PARA 0/1/2; live `0x34 04 <0..2>` updates GUI without echo.
2. ARP ON/OFF live receive confirmed: `0x34 06 01/00`; captured 0x37 dumps do not carry this live state.
3. Sequencer transport confirmed: MIDI realtime `FA` = PLAY/START, `FC` = STOP. Editor PLAY/STOP uses these messages; incoming FA/FC updates GUI.
4. Physical SEQ and REC mode buttons produced no monitor-visible command; no mapping is invented for them.

## v1.60 release status — 2026-09-11
1. v1.60 is packaged from the validated bug-fix working source based on v1.59.
2. Voice Mode is user hardware-confirmed working in v1.59.
3. User hardware/UI findings from v1.59: ARP ON/OFF and PLAY/STOP were one-way; ADSR editing felt heavy; Piano Roll notes were not visually full-step; CLEAR skipped confirmation; Matrix long list interaction was impractical; Library hardware content crossed left while scrolling; LOCAL folder area was too narrow; SONG tree lacked drag/drop to slots.
4. Working fixes now address all GUI issues above plus an evidence-backed ARP reverse send. PLAY reverse remains hardware-unresolved beyond outgoing FA/FC.
5. No SEQ/REC command was invented. Full 64-step hardware sequence read and STORE/0x28 remain unresolved/locked.

## v1.61 release status — 2026-09-11
1. v1.61 is the UI/sequencer refinement pass based on v1.60.
2. Software/headless validation covers fixed window scale presets, contextual top-bar routing, SEQ cleanup, perceptual envelope marker timing, modulation Amount overlay/tooltip, LIBRARY horizontal navigation, SONG tree scrolling, and SONG drop assignment.
3. Existing hardware-confirmed SYNTH behavior is intentionally preserved. No new hardware claim is made for PLAY/STOP editor -> UNO or full hardware sequence read.

## v1.62 — UI scale base correction (2026-09-12)
- Current design base: 1600×900.
- UI scale presets: 50%=800×450, 75%=1200×675, 100%=1600×900, 125%=2000×1125, 150%=2400×1350.
- 100% now maps exactly to design scale 1.0.
- Build remains cumulative and includes the read-only 0x29 hardware sequence work prepared from v1.61.
- STORE/write path remains locked.

## v1.63 — 2026-09-12
- Working build based cumulatively on v1.62.
- Scale presets: 1200×675 / 1440×810 / 1600×900 + fullscreen; design base 1600×900.
- Library navigation/load behavior, ALL metadata caching, 3+2 column layout, SONG file-only highlight, FILL feedback, and one-value-per-parameter-per-step automation UI are integrated.
- Hardware test reported 0x29 sequence decode works but all slots returned preset 001 under the old hard-coded 00 00 request. v1.63 encodes selected slot into the two 7-bit address bytes; hardware confirmation for slots other than 001 is pending.
- STORE remains locked.

---

# v1.64 ADDENDUM — 2026-09-12

## v1.64 — 2026-09-12
Baseline: cumulative v1.63 plus the UI/protocol fixes agreed on 2026-09-12.

### UI scale / window
- Internal design geometry restored to 1600×1000 (v1.60 proportions are the reference).
- Presets: 100%=1200×675, 125%=1440×810, 150%=1600×900.
- Scale changes apply immediately.
- Fullscreen entry removed from UI Scale; standard Windows resize/maximize is enabled.
- UI Scale moved from Settings to the top-bar `⛶` menu.

### SYNTH
- Oscillator layout: OSC1 | NOISE / OSC2 | OSC3.
- OSC1/2/3 LEVEL faders moved into NOISE together with NOISE level.
- NOISE artwork removed; RING/SYNC2/SYNC3 are a compact vertical button stack.

### Keyboard
- Border and heading removed.
- Keyboard is 3 octaves and uses the full panel height.
- Pitch and Mod labels removed; both controls use enlarged paired animated strips.
- Octave uses stacked up/down arrows.
- Pitch Bend Range is a step selector: 2,4,6,8,12,24.
- Lower key corners are slightly rounded.
- Keyboard is part of layout (not an overlay), preventing MOD MATRIX overlap/cropping.

### Settings
- Removed: UI Scale, Preview, Soft Thru, Knob Behavior, Pitch Bend Range, Master Tuning.
- MIDI Interface moved below SYNC in left column.
- Right column is ABOUT.

### Library / Song
- Tabs order: SYNTH, ARP + SEQUENCER, LIBRARY, SONG.
- Library: 3 visible LOCAL columns + 2 right-panel columns with wider separation and right-panel inner frame.
- Arrow navigation is 2D and horizontal viewport follows keyboard selection.
- Library click/arrows only select; Enter loads/previews. Top preset selector is unchanged.
- ALL metadata is cached per scan to reduce repeated metadata reads.
- SONG tree highlights files only, not folders.

### Sequencer
- Sequence source text under SEQUENCER remains removed.
- Automation lane has scale labels 100 / 50 / 0 / -50 / -100 on the left.
- Automation model/UI keeps one value per parameter per step; multiple different parameters may exist on one step.
- FILL pressed indication is held long enough to be visible.
- Software sequencer can transmit MIDI Clock F8 at 24 PPQN while playing, bracketed by FA/FC. Tempo currently follows the Song tempo model (120 BPM default).

### Hardware sequence read
- 0x29 request carries selected preset bank/program.
- 0x29 response parser no longer hard-codes bank/program 00/00 and validates against the requested slot.
- Real preset-001 capture still decodes exactly as before. Presets 2+ require hardware confirmation.

### Safety
- STORE / command 0x28 remains LOCKED. No permanent bulk-write path was enabled.
