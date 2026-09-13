# UNO Synth Pro Editor — MASTER TASK LIST

Updated: 2026-09-08
Baseline: v1.47
Status: `[ ]` open · `[~]` implemented but needs validation · `[x]` completed/frozen · `[?]` research/not confirmed

## P0 — CRITICAL / before the next reliable release

### Preset / storage
- [~] **Fix SAVE sound-state persistence.** Devin v1.47 static audit reports `Preset.params` is not populated from `self.values`, `self.choice`, `self.toggle`; verify in source and implement `_collect_params()` (or equivalent) so SAVE preserves synth state, not only name/number/sequence.
- [~] **Close local preset save→load cycle.** Implement/apply preset parameters back to editor (`_apply_params()` or equivalent). LIBRARY selection/loading must actually restore saved editor state; preserve binary-safe handling of official opaque `.unosyp`.
- [~] **Resolve real Windows Known Folder Documents.** Stop relying on `Path.home()/Documents`; use the actual system Documents location consistently for LIBRARY / SONG / LIVE / SAVE.
- [~] **LIBRARY real `*.unosyp` discovery.** Verify real files appear in UI; rescan/invalidate cache on startup, LIBRARY entry and file mutations.
- [~] **Cache library filesystem scan.** Do not `rglob`/parse all presets on every redraw/mouse movement. Cache and invalidate after relevant file changes / directory changes.
- [ ] **SONG/LIVE real file discovery.** `[System Documents]\\IK Multimedia\\UNO Synth Pro\\songs`, extension `*.unosong`; SONG uses dedicated LOAD SONG, LIVE lists songs only.
- [~] **Persist LIVE slots.** Devin audit reports 4×16 `live_slots` currently live only in memory; save/restore them through appropriate settings/song data.

### INIT / protocol safety
- [~] **Audit and fix INIT Bank Select/Mod Wheel.** Devin audit reports `_defaults()` assigns 64 broadly and `init_patch()` may send CC0 BANK=64 and MOD_WHEEL=64. BANK must never be included accidentally in bulk parameter initialization; MOD_WHEEL default must be intentional.
- [~] **Fix INIT filter-mode enum transmission.** Do not send raw 64 for F1/F2 modes when UI shows LP. Use authoritative filter enum/raw tables so GUI and hardware remain synchronized.
- [ ] **Regression-test INIT on real UNO** after the above fixes: no unintended preset/bank switch, filter modes match GUI, frozen FX mappings unchanged.

### Sequencer
- [~] **Real-UNO sequencer playback validation.** v1.47 has software Note On/Off driven by received MIDI Clock; validate notes/chords, probability, transpose, velocity, gate, tie, active-note flush and step timing.
- [ ] **Internal-clock fallback.** Devin correctly notes v1.47 advancement depends on incoming `0xF8`; add a safe internal timing source when external/UNO clock is absent, tied to tempo/resolution and existing sync policy.
- [ ] **Direction playback.** Audit/fix Forward / Backward / Back'n'Forth; do not assume forward-only stepping.
- [~] **Fix `0x37` sequencer state application.** Devin reports Tie/Accent from current-state SysEx are written into `selected_seq_step`. Verify semantics and prevent READ/current-state reception from corrupting an arbitrarily selected pattern step.
- [ ] **ACC/LENGTH playback behavior.** Audit participation in software playback without inventing hardware mappings.
- [ ] **Current-step indicator.** Visually validate/fix visibility.
- [x] **Fix SEQ_LEN cycling edge case.** Remove dead `if False` branch and make index lookup robust if current length is not in options.

### Preset synchronization / UI
- [~] **Bidirectional preset selector sync.** Editor→UNO Bank/Program and UNO→Editor selector/GUI without echo; v1.47 implementation needs real hardware validation.
- [~] **LFO1/LFO2 FADE IN.** Label exactly `FADE IN`; default OFF; zero displays `OFF`; official CC46/CC50; do not disturb other LFO behavior.
- [ ] **SONG COPY/PASTE.** Devin audit reports release buttons are `lambda: None`; either implement correctly or remove/disable deliberately until implemented.
- [ ] **STORE remains locked.** Do not enable permanent hardware write until bulk-write/store protocol is sufficiently verified.

## P1 — PRIMARY RESEARCH / required for full hardware integration
- [?] **Decode 10-byte flash sequencer step record** at `0x101 + step*10` across all 8192 factory steps. Current structure: `+0 control`, then 3×(Note, Velocity, extra).
- [?] **Map hardware LENGTH** (0.1–64) to state/flash/protocol. Per-note extras are candidates, not confirmed.
- [?] **Find editable VELOCITY representation** in state/flash if present; incoming Note On velocity is separate.
- [?] **Map saved Gate/Tie/Accent representation in flash.** Never copy confirmed 309-byte masks directly to flash `+0`.
- [?] **Finish exact 309-byte state packing/serialization decode.**
- [?] **Understand SysEx `0x28` bulk write/store** from existing captures; determine payload transform and safe use before STORE.
- [?] **Understand `.unosyp` binary format** and relation to current-state SysEx / `0x28` / 4096-byte flash slot.
- [?] **Decode ENV candidates** `0x04B–0x055` and `0x056–0x060`.
- [?] **Decode seq/ARP metadata** `0x381–0x3A1`.
- [?] **Investigate remaining SysEx** (`0x23/0x24/0x34/0x35/...`, external `0x36`) with CONFIRMED/STRONG/NOT CONFIRMED labels only.

## P2 — SECONDARY / robustness, maintainability, completeness
- [ ] **Improve `send_sysex` error handling.** Check `midiOutLongMsg` result at the correct point; avoid misleading timeout/error reporting.
- [ ] **Unify logging.** Replace stray `print` in `MidiOut.send_system_message` with project logging.
- [ ] **Review WinMM callback buffer handling.** Devin flags `midiInAddBuffer` from callback as a theoretical Windows callback/deadlock risk. Treat as risk requiring documentation/source validation, not a confirmed bug.
- [x] **Remove storage import side effects.** Do not create Documents directories merely by importing `storage.py`; initialize paths/directories explicitly.
- [x] **Atomic settings writes.** temp-file + replace/rename to reduce corrupted `settings.json` risk.
- [ ] **Centralize protocol enums.** Remove duplicated FX/filter raw tables from `app.py`; `protocol_map.py` is authoritative.
- [ ] **Replace silent `except Exception: pass` where practical** with useful logging/recovery.
- [ ] **Remove `__pycache__` and obsolete generated files from release ZIP.**
- [ ] **Establish repeatable tests.** Keep tests under Docs per project rule; add regression coverage for storage, INIT, sequencer, paths and frozen MIDI enums.
- [ ] **Full `.unosyp` semantic import/export** after format decode.
- [ ] **Complete hardware preset/library transfer workflow** once safe write protocol is known.
- [ ] **Sequencer hardware-state integration** beyond software playback once mappings are proven.
- [ ] **SONG end-to-end validation.**
- [ ] **LIVE end-to-end validation.**
- [ ] **Final topbar cleanup:** `SYNTH | ARP + SEQUENCER | SONG | LIBRARY`; right `SAVE | STORE | SETTINGS`; READ service/dev only; no LOAD/RESTORE.
- [ ] **Final UI regression:** scaling, keyboard overlay, dropdowns, ENV drag, numeric entry, popups, no shake/cropping.
- [ ] **Code architecture refactor — AFTER functional stabilization.** Split monolithic `app.py` into sensible modules only after P0 is stable; do not mix a broad rewrite with critical functional fixes.
- [ ] **Code hygiene pass** after stabilization: explicit imports, formatting/readability, remove dead/unused code.

## DOCUMENTATION / PROJECT CONTROL
- [ ] Maintain `PROJECT_STATE.md`.
- [ ] Maintain `MIDI_REFERENCE.md`.
- [ ] Maintain `SYSEX_PROTOCOL.md`.
- [ ] Maintain `PRESET_FLASH_FORMAT.md`.
- [ ] Maintain `UPDATER_DFU_RESEARCH.md`.
- [ ] Maintain `HARDWARE_TEST_RESULTS.md`.
- [ ] Maintain `GUI_SPEC.md`.
- [ ] Maintain `FILE_FORMATS_PATHS.md`.
- [ ] Maintain `BUILD_RULES.md`.
- [ ] Maintain `RESEARCH_INDEX.md`.
- [ ] Keep `UNO_TEST_DATA_ALL.md` as raw/full research archive.
- [ ] Maintain `FIXED_CHANGES.md` as the cumulative register of user-fixed decisions (`PENDING / IMPLEMENTED / FROZEN / CANCELLED`).
- [ ] **Before every build, review the entire conversation interval from the previous actual build through the explicit new build command**, then reconcile it against `FIXED_CHANGES.md`, this task list and `PROJECT_STATE.md`.

## COMPLETED / FROZEN — do not redo unless explicitly requested
- [x] FX hardware mappings v1.45: MOD CC95 = 0/42/84; REVERB CC107 = 0/32/64/96; DELAY type = 0/25/50/75/100; tested FX faders/submodes frozen.
- [x] Incoming MIDI responsiveness: ~10 ms queue slices + same-parameter CC coalescing; Clock/Note/SysEx excluded.
- [x] Numeric entry: persistent double-click editor; Enter apply / Esc cancel.
- [x] Parameter popups: mouse near cursor; hardware-origin near control.
- [x] ENV whole-line/segment interaction with ~6–8 px tolerance.
- [x] DELAY TIME R separate fader and DELAY layout corrections.
- [x] LIVE delayed-start control OFF→5…55 sec→1 min; cancel/stop; persistence in v1.47.
- [x] Smooth Canvas scaling / stable keyboard-overlay architecture.
- [x] Virtual keyboard mouse + incoming Note On/Off behavior; pitch/mod strips.
- [x] SYNTH RANDOM v1.46 accepted/frozen.
- [x] INIT intended behavior is defined: reset patch + validated live defaults, no permanent store. **Implementation now has P0 audit fixes above; do not mark implementation fully validated until retested.**
- [x] Confirmed 309-byte state fields: Direction byte219 mask `0x30`; Gate bytes220/221; Tie byte220 `0x10`; Accent byte223; preserve composite bits.
- [x] Updater static research / boot SysEx / DFU mechanism and payload extraction.
- [x] Preset DFU flash map: 4096-byte slots; factory slot structure documented.
- [x] 64×10-byte flash sequencer block identified at `0x101–0x380`.
- [x] Official MIDI Chart incorporated into project reference.
- [x] Unified raw research archive established.

## DEVIN v1.47 AUDIT — disposition
Accepted into P0 after static-audit evidence:
- SAVE state gap; no closed local load cycle.
- INIT BANK/MOD_WHEEL/filter enum hazards.
- external-clock-only sequencer advancement.
- suspicious `0x37` Tie/Accent → selected step behavior.
- redraw-time library I/O.
- LIVE slots not persisted.
- SEQ_LEN dead/fragile branch.
- SONG COPY/PASTE placeholders.

Accepted into P2:
- SysEx error-order handling, logging consistency, storage import side effects, atomic settings, enum deduplication, silent exceptions, release/test hygiene.

Risk only / verify before changing:
- WinMM `midiInAddBuffer` callback concern.

Deferred deliberately:
- broad `app.py` rewrite/formatter pass until functional P0 work is stable.

## BUILD / RELEASE GATE
- [ ] Build only on explicit user command **“Сделай сборку”** or equivalent explicit build authorization.
- [ ] Every build is cumulative.
- [ ] Before ZIP: review conversation since previous build; reconcile FIXED_CHANGES + TASKS + PROJECT_STATE.
- [ ] Syntax check + launch smoke + cumulative checklist + ZIP integrity.
- [ ] Test actual preset/song discovery, not merely path strings.
- [ ] Regression-check frozen FX/MIDI.
- [ ] Root contains runtime/source only; tests/validation go in Docs.
- [ ] Update all relevant project knowledge docs.
- [ ] Never modify archived/reference v1.29 unless explicitly requested.

## CURRENT WORK ORDER
1. P0 storage/preset cycle: real Documents + SAVE/LOAD state + library cache/discovery.
2. P0 INIT protocol-safety fixes and real-UNO regression.
3. P0 sequencer: internal/external clock, direction, `0x37` corruption guard, real-UNO playback validation.
4. LFO FADE IN + bidirectional preset sync validation + LIVE persistence / SONG placeholders.
5. Continue 10-byte flash research: LENGTH / control byte / persisted Gate-Tie-Accent.
6. Decode `0x28` / `.unosyp` sufficiently for safe STORE.
7. SONG/LIVE end-to-end, final UI regression, then maintainability/refactor work.

This file is the authoritative project task checklist. New findings go here; completed items become `[x]`.

## v1.49 test targets
- [~] Verify real `.unosyp` discovery from `[System Documents]\IK Multimedia\UNO Synth Pro Editor`.
- [~] Verify automatic UNO Synth Pro MIDI IN/OUT selection and reconnect.
- [?] Discover hardware preset-name/catalog acquisition.

## v1.50 hardware test targets
- [~] Validate both Library panels can independently switch LOCAL/HARDWARE.
- [~] Validate LOCAL folder navigation and real `.unosyp` visibility.
- [~] Validate HARDWARE continuous 001–256 scrolling/selection.
- [~] Validate main selector defaults to HARDWARE and local-folder arrow navigation.
- [~] Validate incoming UNO Program Change returns selector/source to HARDWARE and highlights the correct number.
- [ ] Preview official binary `.unosyp`: still P0/open; do not guess unsafe SysEx.
- [ ] Hardware preset names/catalog: still P0/open.
- [ ] Library sorting/tags/genres: deliberately deferred as a separate design task.

## v1.51 update — 2026-09-08
- [x] Confirm hardware preset-name read protocol `0x24` and implement 001–256 read-only catalog acquisition.
- [x] Display returned hardware names in Library and main preset selector/tree.
- [x] On hardware preset changes, automatically request `0x37` state and current `0x24` name using test3-confirmed timing/order.
- [x] Add non-stalling catalog retry/skip behavior for a dropped `0x24` response.
- [x] Enlarge LOCAL folder disclosure triangles.
- [~] Decode remaining 309-byte state fields so SYNTH GUI restores from hardware preset changes. v1.52 applies exact real-hardware LUT signatures for 83/87 scanned CC fields; real-UNO preset regression and remaining/context-dependent fields are still required.


## v1.52 update — 2026-09-09
- [x] Full State Mapper hardware sweep captured 87 known preset CCs at 128 points each (11,136 state captures) with full 309-byte replies.
- [x] Differential map built for 83 scanned CC fields; exact observed signatures and bit masks retained.
- [x] Runtime exact-observed `0x37` decoder integrated; no guessed/nearest fallback.
- [~] Real-UNO regression: switch multiple factory presets from both editor and hardware and confirm visible SYNTH controls follow.
- [?] Resolve CC7 and CC110/111/112 in a scan context where their parameters are active.
- [?] Decode any unseen higher-resolution signatures and remaining GUI controls not covered by the known CC list.


## v1.53 update — 2026-09-09
- [x] Replace CHORUS mode dropdown with horizontal SYNTH1/SYNTH2/STRINGS buttons, ordinal mapping 1:1.
- [x] Replace PHASER color dropdown with horizontal COLOR1/COLOR2 buttons, ordinal mapping 1:1.
- [~] Hardware test third-level state visibility via preset switching; do not infer unknown PHASER state semantics.
- [x] Supersede ENV segment dragging with point-only editing; hide edit points until hover/drag.
- [~] Add separate live envelope-position marker for visual modulation tracking; validate feel/timing on real use.
- [x] LOCAL Library first-level folders only; recursively flatten all nested `.unosyp`; exclude songs.

## v1.54 update — 2026-09-10
- [x] Restore LOCAL Library left-click load path so saved editor-native preset parameters actually rebuild the GUI.
- [x] Implement LOCAL current-buffer preview via confirmed live CCs, with no Program Change and no STORE/0x28.
- [x] Keep existing UNO/HARDWARE Library preset switching untouched.
- [x] Make preset context menu right-click only; remove Load; inline Favorite + seven color tags in a dark menu.
- [x] Remove preset icons and Add Folder toolbar icon; retain folder New/Rename/Copy/Cut/Paste/Delete context commands.
- [x] Main selector LOCAL label = preset name only; device source label = `UnoSynth`; remove READ topbar button.
- [ ] Hardware validate v1.54 LOCAL preview against several editor-native saved presets, especially context-dependent FX controls.
- [?] Official opaque/binary IK `.unosyp` semantic preview remains blocked on safe format decode.


## v1.55 — LOCAL binary preview test (2026-09-10)
- TEST/NOT YET HARDWARE-CONFIRMED: official UNO Synth Pro binary `.unosyp` matching header `25 01 00 00` and expected payload length may be previewed using externally documented current-buffer SysEx `0x36`; no Program Change, STORE or `0x28` is sent.
- After `0x36`, editor requests current state `0x37` so confirmed decoder fields can rebuild GUI from the UNO response.
- SAFETY: malformed/unexpected binary files are rejected rather than transmitted. This `0x36` path must remain TEST until reproduced on the user's real UNO.
- UI: preset context menu Favorite star is always yellow; seven smaller anti-aliased circular tags are shown directly in one row. Library tag dots use anti-aliased rendering.


## v1.57 update — 2026-09-10
1. [x] Integrate read-only `.unosyp` 64-step decoder into LOCAL preset load and `Preset.sequence`.
2. [x] Preserve decoded sequence when optional binary synth preview is attempted.
3. [x] Settings Preview first-run default ON + dirty APPLY workflow.
4. [x] Restore SONG folder-tree/content selection in the SONG page.
5. [x] Main selector no source/path prefix; `UnoSynth` device source label retained.
6. [x] Tags submenu = yellow star + seven colored circles; add preset-name/tag spacing.
7. [x] Library horizontal scroll drag + Shift-wheel; clip/mask cross-panel overflow.
8. [x] Drag ghost + valid target feedback.
9. [x] Preset `↑ UP` / `↓ DOWN` one-place local metadata ordering, with boundary commands disabled.
10. [x] Filter ENV full positive visual range for +64.
11. [x] Envelope live marker Attack → Decay → Sustain hold → Release path, including short Attack.
12. [!] Hardware VOICE mode receive remains unimplemented because no confirmed mapping exists in current captures/docs.
13. [!] Matrix Source/Destination hardware receive remains unimplemented because current project evidence explicitly leaves those mappings unconfirmed.
14. [x] Preserve STORE/0x28 lock and frozen v1.45 FX mappings.


## v1.58 pre-test build gate — 2026-09-10
1. [x] Reconcile accepted v1.57 ZIP against post-v1.57 working source; only intended new state/ARP/Matrix additions are carried forward.
2. [x] Regression-test `.unosyp` test2/test3/test4 synth-state + supported sequence and test5 state-only behavior.
3. [x] Headless LOCAL binary load verifies representative OSC/filter/FX mapper path plus Voice/ARP/Matrix read-side fields.
4. [x] Factory slot59 Mod Matrix cross-boundary Source/Destination/Amount regression test added and passing.
5. [x] ARP `0x3E` receive + `0x3C` Pattern send + native Range 1..4 software tests added and passing.
6. [x] Confirm hardware preset sync architecture remains Program Change/`0x32` -> `0x37` -> `0x24`; sequence is explicitly outside `0x37` scope.
7. [x] STORE/DEPLOY lock audited; runtime has no `0x28` SysEx constructor; `0x36` remains experimental only.
8. [x] Hardware state-only sequence provenance added; stale LOCAL notes cleared on hardware preset switch; sequencer page warns `64 STEPS NOT READ`.
9. [x] Compile/import/headless page draw, no-MIDI-echo and protocol regression checks passing.
10. [x] v1.58 source/version/docs prepared for packaging.

## Still open after v1.58 test build
1. [ ] Real-hardware validation of v1.58 on UNO Synth Pro.
2. [ ] Discover safe full hardware preset/sequence read; do not assume `0x37` contains sequence.
3. [?] Research-only: determine exact packed-state 10-bit Matrix Fade In read-side scale if needed; current Matrix Fade In control itself is user-confirmed working and must not be changed speculatively.
4. [ ] Hardware-differential-confirm Voice Mode MONO/LEGATO/PARA mapping.
5. [ ] Hardware-confirm or reject experimental `0x36` current-buffer load before promoting it from TEST.


## ADSR visual animation target — fixed 2026-09-11
1. [ ] Rework FILTER ENV and AMP ENV graph geometry to an Equator2-style visual response without changing MIDI/raw ADSR values.
2. [ ] Attack: first clearly visible graph movement should begin around the equivalent of 20 ms, not the current roughly 75 ms visual threshold.
3. [ ] Decay: first clearly visible graph movement should begin around the equivalent of 20 ms, not the current roughly 75 ms visual threshold.
4. [ ] Sustain: below roughly 3% it may visually collapse to the entry point; from roughly 3% upward the S→R portion must become a horizontal sustain line whose vertical position follows the S value.
5. [ ] Release: first clearly visible graph movement should begin around the equivalent of 20 ms, not the current roughly 75 ms visual threshold.
6. [ ] Use a nonlinear/log-like time-to-X visual mapping for A/D/R so short times are distinguishable while long times still fit the graph.
7. [ ] This is a GUI/animation mapping change only. Do not alter confirmed ADSR MIDI ranges, CC values, preset-state decoding, hardware synchronization, or envelope editing semantics.
8. [ ] Preserve the existing live envelope-position marker behavior; adapt only its path geometry to the revised ADSR curve.

## v1.59 implementation pass — current status 2026-09-11
1. [~] ADSR graph: nonlinear short-time visual response for A/D/R implemented in working source; needs visual/user validation.
2. [~] ADSR editing: AD horizontal; DS horizontal+vertical; SR line vertical; R horizontal implemented in working source; needs visual/user validation.
3. [~] LIBRARY HARDWARE: multi-column layout + horizontal scrollbar implemented in working source; needs UI validation.
4. [~] LIBRARY LOCAL/HARDWARE: mouse wheel scrolls the panel under the cursor; implemented in working source; needs UI validation.
5. [~] LIBRARY LOCAL: long names clipped with ellipsis; implemented in working source; needs UI validation.
6. [~] LIBRARY LOCAL: left-click folder no longer opens context menu on release; implemented in working source; needs UI validation.
7. [~] LIBRARY keyboard arrow navigation for LOCAL/HARDWARE implemented in working source; needs UI validation.
8. [~] SONG preset selector replaced by a simple expandable tree; single click opens/closes folders; arrow navigation retained. Needs UI validation against the requested pre-v1.47 behavior.
9. [~] Sequencer Piano Roll: one click selects existing note; double-click deletes existing note; implemented in working source.
10. [~] Sequencer LENGTH visually stretches/shrinks the note rectangle in Piano Roll according to stored step length; implemented in working source. Hardware LENGTH semantics remain research/unconfirmed.
11. [~] Sequencer CLEAR confirmation with in-theme `ДА` / `НЕТ` implemented in working source.
12. [x] Remove erroneous `ARP_RATE` editor control/value. UNO Synth Pro has no ARP RATE hardware parameter; do not map it to CC/SysEx or reintroduce it as a device control.
13. [~] LFO Fade In default `OFF` implemented in editor defaults for LFO1/LFO2.
14. [~] Filter graph LFO animation path preserved through Matrix LFO→Filter Cutoff modulation; verify visually in user test.
15. [~] Matrix dropdown wheel capture implemented: open dropdown consumes wheel; Matrix beneath does not move.
16. [~] Current preset session persistence implemented: save LOCAL path/HARDWARE slot on exit and restore without MIDI transmission at startup.
17. [ ] Voice Mode hardware mapping: FAIL on paraphonic preset; re-reverse-engineering required.
18. [ ] ARP ON/OFF hardware synchronization: missing mapping.
19. [ ] SEQ ON/OFF hardware synchronization: missing mapping; hardware state can change via both SEQ and PLAY.
20. [ ] Full hardware 64-step sequence read remains unresolved.
21. [~] v1.57 LOCAL/HARDWARE/LOCAL stall was reproduced; repeated v1.58 test did not reproduce it. Keep under longer validation.
22. [x] Matrix Fade In control/function is user-confirmed working. Preserve it. [?] Packed-state `fade_raw` read-side scaling remains research-only; do not map guessed raw values to GUI.
23. [ ] `0x28` STORE remains locked.


## Matrix Fade In status clarification — 2026-09-11
1. [x] Current Matrix Fade In behavior is user-confirmed working.
2. [x] Remove Matrix Fade In from the active v1.59 bug/fix list.
3. [?] Keep only the separate packed-state `fade_raw` decode/scale question as protocol research; it must not block the working control or trigger speculative remapping.

## 2026-09-11 v1.59 protocol updates
1. Voice Mode receive confirmed: raw byte 175 bits 5-6 = MONO/LEGATO/PARA 0/1/2; live `0x34 04 <0..2>` updates GUI without echo.
2. ARP ON/OFF live receive confirmed: `0x34 06 01/00`; captured 0x37 dumps do not carry this live state.
3. Sequencer transport confirmed: MIDI realtime `FA` = PLAY/START, `FC` = STOP. Editor PLAY/STOP uses these messages; incoming FA/FC updates GUI.
4. Physical SEQ and REC mode buttons produced no monitor-visible command; no mapping is invented for them.

## v1.60 bug-fix pass — packaged release 2026-09-11
1. [~] ARP ON/OFF reverse send via captured official-editor `35 00 <state>` implemented; hardware validation required.
2. [?] PLAY/STOP reverse: editor sends FA/FC, but user reports hardware does not react in the reverse direction. Keep open; do not invent an extra command.
3. [~] ADSR drag responsiveness optimized to one redraw/send pass per motion; user validation required.
4. [~] Piano Roll one-step note width corrected; new Step default LENGTH = 1.0; user validation required.
5. [~] CLEAR confirmation wiring corrected; user validation required.
6. [~] Matrix Source/Destination replaced with large multi-column Parameter Picker with hover highlight/current-value check; user validation required.
7. [~] Library HARDWARE cross-panel scroll drawing blocked for partially visible columns; user validation required.
8. [~] Library LOCAL folder pane widened and folder names clipped with ellipsis; user validation required.
9. [~] SONG tree preset drag/drop to SONG slots implemented; user validation required.
10. [x] Software/headless gates: compileall, v1.58 regression, v1.59 regression, v1.60 regression and all-page redraw smoke pass.

## v1.64 follow-up hardware validation
- Verify 0x29 preset 2+ response bank/program and sequence data on device.
- Verify generated MIDI F8 clock starts/moves UNO hardware SEQ under external/USB sync.
- Confirm PB Range hardware semantics before implementing any transmission.
