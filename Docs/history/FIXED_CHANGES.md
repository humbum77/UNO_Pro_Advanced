Current: **v0.9.2-beta**. [Requested rollback](RELEASE_NOTES_v0.9.2-beta.md) supersedes the historical notes below.

# Current release: v0.9.0-beta

The post-FIX2 changes are implemented in this build. See [release notes](RELEASE_NOTES_v0.9.0-beta.md) and [validation](VALIDATION_v0.9.0-beta.md) for current status. Earlier statements below are historical and are superseded by these release notes where they differ. Hardware limitations remain open.

---

# FIXED_CHANGES.md — cumulative fixed decisions

Updated for v1.48. Status: PENDING / IMPLEMENTED / FROZEN / CANCELLED.

## IMPLEMENTED in v1.48
- IMPLEMENTED: use actual Windows Documents (redirected/OneDrive aware) for project storage; apply consistently through storage paths used by LIBRARY/SONG/LIVE/SAVE.
- IMPLEMENTED: SAVE local editor preset includes current `values`, `choice`, `toggle`, `filter_link`; local JSON `.unosyp` can restore those editor parameters.
- IMPLEMENTED: official/opaque binary `.unosyp` is not guessed or rewritten; semantic support remains locked until decoded.
- IMPLEMENTED: Library preset scan cached; file mutations invalidate cache.
- IMPLEMENTED: LIVE 4x16 slot assignments persist in settings.
- IMPLEMENTED: INIT excludes BANK and MOD_WHEEL from bulk default CC sending; filter/FX enum values use authoritative protocol tables.
- IMPLEMENTED: 0x37 current-state receive no longer writes Tie/Accent into whichever sequencer step happens to be selected.
- IMPLEMENTED: SEQ_LEN cycling no longer contains the dead/fragile `if False` branch.
- IMPLEMENTED: LFO1/LFO2 label is exactly `FADE IN`; default zero is OFF and popup displays OFF. Official CC46/CC50 retained.
- IMPLEMENTED: settings writes are atomic and storage import no longer creates project directories as a side effect.

## FROZEN — preserve
- FROZEN: v1.45 hardware FX enums: MOD CC95 0/42/84; DELAY type 0/25/50/75/100; REVERB CC107 0/32/64/96.
- FROZEN: incoming MIDI ~10 ms queue/coalescing behavior; Clock/Note/SysEx not coalesced.
- FROZEN: numeric entry, mouse/hardware popups, ENV segment interaction, DELAY TIME R/layout, stable Canvas scaling, keyboard overlay, virtual keyboard, SYNTH RANDOM.
- FROZEN: confirmed 309-byte fields: Direction byte219 mask 0x30; Gate 220/221; Tie byte220 mask 0x10; Accent byte223; preserve composite bits.
- FROZEN: STORE / destructive bulk write remains locked until 0x28 is validated.
- FROZEN: archived/reference v1.29 is never modified unless explicitly requested.

## PENDING after v1.48
- PENDING: real-Windows validation of Known Folder path and real `.unosyp`/`.unosong` discovery.
- PENDING: real-UNO regression of INIT and bidirectional preset synchronization.
- PENDING: sequencer internal-clock/direction work and real-UNO playback validation.
- PENDING: SONG COPY/PASTE semantics/implementation.
- PENDING: full official binary `.unosyp` decode and safe STORE research.

## BUILD RULE
Before every build, review the complete conversation interval since the previous actual build, reconcile it with this file, `UNO_PROJECT_TASKS.md`, and `PROJECT_STATE.md`, then run cumulative validation. Build only after explicit user authorization.

- IMPLEMENTED: Startup logging must not crash when the UNO Synth Pro Documents folder does not yet exist; create directories explicitly at startup and fall back to stderr if file logging is unavailable.

## v1.49
- IMPLEMENTED: Local Library root corrected to `[System Documents]\IK Multimedia\UNO Synth Pro Editor`.
- IMPLEMENTED: MIDI IN/OUT default preference is `UNO Synth Pro`; startup scans ports and selects exact/containing `UNO Synth Pro`.
- IMPLEMENTED: MIDI connection settings save/apply without APPLY.
- IMPLEMENTED/FROZEN: Program Change always ON; PR CHANGE switch removed.
- FROZEN: MIDI CLOCK default OFF pending sequencer sync completion.
- PENDING: Hardware preset-name/catalog acquisition from UNO Synth Pro.

## v1.50
- IMPLEMENTED: Library redesigned as a two-panel preset/file manager.
- IMPLEMENTED: Each Library panel independently selects LOCAL or HARDWARE.
- IMPLEMENTED: LOCAL uses the real folder hierarchy under `[System Documents]\\IK Multimedia\\UNO Synth Pro Editor`; genre/category sorting removed from the Library UI.
- IMPLEMENTED: HARDWARE is one continuous 001–256 slot list; no page model in Library.
- IMPLEMENTED: PREVIEW control moved out of Library into global SETTINGS.
- IMPLEMENTED: Main preset selector defaults to HARDWARE and opens a source/folder tree; HARDWARE is first.
- IMPLEMENTED: Main arrows follow the current source: HARDWARE changes adjacent hardware slots; LOCAL changes adjacent `.unosyp` files in the selected folder.
- FROZEN/HARDWARE CONFIRMED: preset-number synchronization works both directions. Hardware preset names/catalog are still unavailable.
- PENDING: true semantic Preview of official opaque/binary `.unosyp` remains locked until a safe current-buffer load format/command is confirmed. Moving the Preview setting does not invent a protocol.
- PENDING: hardware preset names/catalog acquisition.
- DEFERRED: sorting, genre classification, tags, favorites and ratings; these require a separate Library metadata design.

## v1.50 HOTFIX
- IMPLEMENTED: missing `storage.child_folders()` added for two-panel LOCAL Library.
- IMPLEMENTED: missing `storage.local_folders()` added for the main preset-selector tree.
- VALIDATED: the service `songs` folder is excluded from the LOCAL preset folder tree.

## v1.51
- IMPLEMENTED: read-only HARDWARE preset-name catalog using confirmed `0x24` requests/responses for slots 001–256.
- IMPLEMENTED: HARDWARE names are shown in the continuous Library list and main preset selector/tree.
- IMPLEMENTED: preset changes from editor or UNO schedule confirmed read-only sync: `0x37` current-state request and `0x24` current-name request.
- IMPLEMENTED: incoming Program Change remains authoritative for selected hardware slot; `0x32` is treated as a current-preset notification and triggers refresh without echoing writes.
- IMPLEMENTED: startup requests current state and begins sequential 256-slot name catalog acquisition; catalog has one retry per missing name response so a dropped packet does not permanently stall the scan.
- IMPLEMENTED: LOCAL folder disclosure triangle enlarged for easier mouse targeting; folder row hit area remains large.
- FROZEN: confirmed bidirectional preset-number behavior is preserved.
- PENDING: full 309-byte state semantic decoding is not yet complete. v1.51 automatically retrieves the new state dump, but applies only already-confirmed state fields; no guessed parameter offsets are introduced.


## v1.52 — 0x37 hardware GUI sync
- HARDWARE CONFIRMED: v1.51 preset-name catalog works on real UNO; preset number changes both directions, but v1.51 GUI parameters stayed stale.
- HARDWARE CONFIRMED: standalone Full State Mapper v1.3 HOTFIX connected through the proven WinMM layer and completed the full 87-controller × 128-point scan without reported scan errors.
- IMPLEMENTED: exact-observed `0x37` LUT decoder generated from the hardware sweep. 83 CC fields have observed state signatures; 4 scan entries had no `0x37` change in that scan context (CC7, CC110, CC111, CC112).
- IMPLEMENTED/SAFETY: v1.52 applies only exact signatures observed in the real-hardware sweep. There is no nearest-signature or guessed fallback; unseen signatures are left unchanged and counted in the status line.
- IMPLEMENTED: `0x37` state reception applies decoded preset fields to GUI without echoing CC writes back to UNO. Confirmed sequencer Direction decoding remains preserved.
- PENDING: hardware validation of v1.52 across factory presets, especially context-dependent Delay/Reverb fields and any unseen higher-resolution signatures.
- PENDING: four no-change scan controls and GUI controls with no confirmed CC/state mapping remain unresolved; do not claim full 309-byte semantic completion yet.

## v1.53 — GUI visibility / Library flattening
- IMPLEMENTED: MODULATION CHORUS third-level control is presented as one horizontal button row: `SYNTH1 | SYNTH2 | STRINGS`.
- IMPLEMENTED: MODULATION PHASER third-level control is presented as one horizontal button row: `COLOR1 | COLOR2`.
- FROZEN: the new buttons preserve the former dropdown ordinal values strictly 1:1; no new MIDI value mapping is invented by the GUI replacement.
- IMPLEMENTED: envelope editing is point-only. The previous whole-segment drag behavior is superseded by the user's new decision.
- IMPLEMENTED: envelope edit points are hidden normally and appear only on hover/while dragging.
- IMPLEMENTED: a separate live envelope-position marker of a different color moves along the ADSR curve for visual modulation tracking; it does not edit or transmit parameters.
- IMPLEMENTED: LOCAL Library exposes only first-level folders. Selecting one flattens all `*.unosyp` files found recursively below it (nested folders are not shown); `songs` remains excluded.
- IMPLEMENTED: main LOCAL preset tree also exposes only first-level folders and flattens nested `*.unosyp` files into the selected first-level folder menu.
- FROZEN: HARDWARE remains a continuous read-only-style selection list 001–256 with confirmed names/number synchronization; STORE remains locked.
- TEST TARGET: use the new CHORUS/PHASER buttons to verify whether hardware preset state is actually decoded for the third-level parameter or whether the old dropdown merely failed to make the received state visible.


## UNO Pro Advanced — Library / envelope / confirmed MOD CC update
- IMPLEMENTED: application/build display name changed to `UNO Pro Advanced`.
- IMPLEMENTED: Library left panel is permanent LOCAL; its tree is narrower and its preset view wider.
- IMPLEMENTED: right panel defaults to UNO. The LOCAL/HARDWARE dropdown is removed; a folder can be opened in the right panel from the left-tree context menu, and the UNO button returns the right panel to device mode.
- IMPLEMENTED: Receive/Send stay in the right toolbar and remain position-stable; they are visually disabled while a LOCAL folder is open on the right.
- IMPLEMENTED: panel-specific controls stay in that panel's toolbar. Folder creation is a compact icon and uses inline naming in the tree. Folder rename/delete/open-right are in the folder context menu.
- IMPLEMENTED: file/folder bullets replaced with folder/preset/tree-state icons.
- IMPLEMENTED: LOCAL `ALL` is the top level and its view recursively shows presets from all subfolders.
- IMPLEMENTED: LOCAL preset views use alphabetic columns with horizontal scrolling when needed.
- IMPLEMENTED: local-only metadata database stores Favorite plus seven color tags without modifying `.unosyp`; tags are shown after preset names and toolbar icons filter the current scope.
- IMPLEMENTED: icon tooltips use a 900 ms hover delay.
- IMPLEMENTED: envelope live marker is small and white; it disappears after Release completes. The marker remains visual-only.
- HARDWARE CONFIRMED/IMPLEMENTED: CHORUS third level sends CC98 values 0/42/84. PHASER COLOR sends CC96 values 0/127.
- FROZEN: permanent hardware STORE remains locked; unrelated pages/protocol behavior are unchanged.

## UNO Pro Advanced — Library interaction/layout refinement (2026-09-10)
- IMPLEMENTED: Library panel fonts increased by 2 pt for tree rows, preset rows, UNO slot rows, toolbar icons and Library context menus.
- IMPLEMENTED: left-panel `LOCAL` label removed.
- IMPLEMENTED: left toolbar keeps Add Folder at the left and moves Favorite + seven color-tag filters to the far right.
- IMPLEMENTED: right toolbar anchors UNO at the far left and Receive/Send at the far right; Receive/Send remain visible but disabled outside UNO mode.
- IMPLEMENTED: right panel width reduced by roughly one third; panel gap fixed at 10 px; freed width is assigned to the left preset view. Left folder tree is narrowed further.
- IMPLEMENTED: LOCAL preset views remain alphabetic columns with horizontal scrolling; the same view renderer is used when a LOCAL folder is opened on the right.
- IMPLEMENTED: a short left click on a LOCAL preset selects it and opens the preset menu (Load, Favorite, seven Tags, Rename, Copy, Cut, Paste, Delete). Mouse movement past the drag threshold starts drag/drop instead of opening the menu.
- IMPLEMENTED: a short left click on a folder selects it and opens the folder menu (Expand/Collapse where applicable, Open in right panel, New folder, Rename, Copy, Cut, Paste, Delete).
- IMPLEMENTED: drag/drop is restored for LOCAL presets/folders between LOCAL destinations. UNO slot -> LOCAL requests the slot state and then saves it to the drop folder. LOCAL -> UNO selects the target slot but permanent write remains blocked by the existing STORE lock.
- FROZEN: no permanent hardware-write bypass was added; STORE remains locked.

## v1.54 — 2026-09-10
- IMPLEMENTED/P0: LOCAL Library preset selection now closes the actual editor-native save→load→preview cycle: load JSON preset params, apply GUI state, then send confirmed live CCs to UNO current state without Program Change or STORE.
- FROZEN: Hardware Library preset selection/sync remains unchanged.
- IMPLEMENTED: LOCAL preset left click is selection/preview only; preset context menu is right-click only.
- IMPLEMENTED: preset context menu is dark; first row is Favorite star + seven smooth circular color tags. Removed `Load`, textual color names and `Tags` submenu.
- IMPLEMENTED: main preset tree/menu is dark; hardware source label is exactly `UnoSynth`; selected LOCAL label shows preset stem only.
- IMPLEMENTED: preset icons removed; Add Folder toolbar icon removed; folder creation stays in context menu.
- IMPLEMENTED: right toolbar `UNO` renamed `Uno` and moved beside Receive/Send on the right.
- IMPLEMENTED: topbar READ removed.
- SAFETY: no `0x28`/permanent preset write enabled. Official binary `.unosyp` semantic preview remains pending.


## v1.55 — LOCAL binary preview test (2026-09-10)
- TEST/NOT YET HARDWARE-CONFIRMED: official UNO Synth Pro binary `.unosyp` matching header `25 01 00 00` and expected payload length may be previewed using externally documented current-buffer SysEx `0x36`; no Program Change, STORE or `0x28` is sent.
- After `0x36`, editor requests current state `0x37` so confirmed decoder fields can rebuild GUI from the UNO response.
- SAFETY: malformed/unexpected binary files are rejected rather than transmitted. This `0x36` path must remain TEST until reproduced on the user's real UNO.
- UI: preset context menu Favorite star is always yellow; seven smaller anti-aliased circular tags are shown directly in one row. Library tag dots use anti-aliased rendering.


## v1.57 cumulative fixed changes — 2026-09-10
1. Settings: PREVIEW defaults ON on first run; settings changes become dirty; one APPLY button persists/applies; no SAVE SETTINGS button.
2. SONG: restored in-page local folder tree + preset contents selector; no Library navigation is required to assign a song preset.
3. Main preset selector: source/path prefix removed; hardware display is preset name only.
4. Hardware source naming: UnoSynth retained.
5. Tags: preset context contains exactly a Tags > submenu with yellow star + seven colored circles.
6. Preset display: explicit gap before tags.
7. Library horizontal scrolling: Shift+wheel and draggable horizontal scrollbar for LOCAL panes.
8. Library content: narrower tree / wider content and off-viewport column suppression retained.
9. Library drag feedback: filename ghost follows pointer after threshold and valid LOCAL targets are highlighted.
10. Preset context: ↑ UP / ↓ DOWN added with persistent local metadata ordering.
11. LOCAL binary .unosyp: 64-step sequence decoder integrated read-only; up to three notes/step, per-note velocity/extra and raw control preserved.
12. Filter ENV visualization: bipolar +64 is treated as +100% of full cutoff range, not +50%.
13. Envelope indicator: begins at attack start on Note On, traverses Attack and Decay, holds at Sustain entry, and releases from the actual level on Note Off.
14. Superseded by v1.58 research: Matrix Source/Destination packed-state decoding is now confirmed by factory slot59 cross-check. Voice Mode remains a high-confidence read-side candidate, not hardware-differential-confirmed. Matrix Fade In scale remains unconfirmed and must not be mapped.
15. STORE/0x28 remains locked.


## v1.58 cumulative fixed changes — 2026-09-10
1. LOCAL binary `.unosyp` state decoder is read-only and reuses the exact `0x37` mapper; no guessed nearest-state fallback.
2. 1081-byte sequence decoding stays enabled; 1084-byte sequence decoding stays disabled until independently proven.
3. GUI must identify sequence provenance. Hardware `0x37` state must never be presented as a complete 64-step hardware sequence.
4. Switching from LOCAL to a different hardware preset clears stale LOCAL sequence notes and marks the hardware sequence unavailable.
5. Matrix Source/Destination read-side formula is frozen to the cross-boundary packing validated against factory slot59. Do not revert Source to `word & 0x1F`.
6. Matrix Fade In raw field is 10 bits at route bits 11..20; semantic scale is unknown, so GUI `MFADE` must not be overwritten from it.
7. ARP Pattern outgoing format is `3C 00 02 <7bit0> <7bit1> <2bit2>`; ARP Range writes 1..4 directly. ARP ON/OFF remains unmapped.
8. STORE/DEPLOY remain locked; no runtime `0x28` sender. `0x36` remains experimental and may only affect the current buffer.


## ADSR graph visual behavior — FIXED DECISION (2026-09-11)
1. PENDING IMPLEMENTATION: FILTER ENV and AMP ENV must use a more responsive Equator2-style graph mapping for short ADSR times.
2. FIXED VISUAL TARGET: Attack visible response begins at approximately 20 ms equivalent instead of the current approximately 75 ms threshold.
3. FIXED VISUAL TARGET: Decay visible response begins at approximately 20 ms equivalent instead of the current approximately 75 ms threshold.
4. FIXED VISUAL TARGET: Sustain becomes a horizontal S→R line from approximately 3% upward; its height follows the Sustain parameter. Below that it may collapse visually near the S entry point.
5. FIXED VISUAL TARGET: Release visible response begins at approximately 20 ms equivalent instead of the current approximately 75 ms threshold.
6. FIXED IMPLEMENTATION RULE: A/D/R graph width uses a nonlinear/log-like visual mapping.
7. FROZEN SAFETY RULE: this changes graph geometry/animation only; it must not change ADSR MIDI/raw values, CC mappings, preset decoding, or hardware synchronization.
8. FROZEN BEHAVIOR: keep the separate live envelope-position marker; its movement follows the new curve geometry after implementation.

## Next-build working implementation — v1.59 candidate, not packaged (2026-09-11)
1. ADSR graph/editor changes, Library columns/navigation/scrolling, SONG tree browser, Piano Roll note selection/deletion/LENGTH visualization, themed sequence CLEAR confirmation, LFO Fade defaults, Matrix dropdown wheel capture, and last-preset session restore have been implemented in the current working source.
2. These items are SOFTWARE/HEADLESS VALIDATED only where covered by `Docs/test_v159_working.py`; they are not yet accepted as a v1.59 release and not hardware validated unless separately listed in `HARDWARE_TEST_RESULTS.md`.
3. CORRECTION: UNO Synth Pro has no ARP RATE hardware parameter. The erroneous `ARP_RATE` editor control/value has been removed from the v1.59 working source; no CC/SysEx mapping is to be assigned.
4. STORE remains locked and no unknown ARP ON/OFF, SEQ ON/OFF, Voice Mode, Matrix Fade, or full hardware-sequence protocol command was invented.


## Matrix Fade In — PRESERVE WORKING BEHAVIOR (2026-09-11)
1. User-confirmed: Matrix Fade In works in current use.
2. It is not a v1.59 defect and must not be rewritten merely because the packed-state `fade_raw` scale remains under-researched.
3. Preserve current UI/control behavior. Any future raw-state receive mapping requires separate evidence and must not regress the working control.

## 2026-09-11 v1.59 protocol updates
1. Voice Mode receive confirmed: raw byte 175 bits 5-6 = MONO/LEGATO/PARA 0/1/2; live `0x34 04 <0..2>` updates GUI without echo.
2. ARP ON/OFF live receive confirmed: `0x34 06 01/00`; captured 0x37 dumps do not carry this live state.
3. Sequencer transport confirmed: MIDI realtime `FA` = PLAY/START, `FC` = STOP. Editor PLAY/STOP uses these messages; incoming FA/FC updates GUI.
4. Physical SEQ and REC mode buttons produced no monitor-visible command; no mapping is invented for them.

## v1.60 bug-fix release — 2026-09-11
1. ARP ON/OFF reverse send implemented from captured official-editor traffic: editor -> UNO `F0 00 21 1A 02 03 35 00 <0|1> F7`; hardware validation still required.
2. Sequencer CLEAR button is wired to the themed `ДА/НЕТ` confirmation instead of direct clear.
3. ADSR drag path groups DS updates into one redraw/send pass to reduce the heavy/laggy feel without changing raw/MIDI ranges.
4. New software sequence notes default to LENGTH 1.0 and Piano Roll renders at least one full step width for a one-step note.
5. Matrix Source/Destination long dropdown replaced by a large multi-column parameter picker: maximum options visible at once, hover highlight, current-value check mark, click-to-select, Esc/click-outside close, no wheel traversal when the full picker is visible.
6. Library LOCAL folder tree widened to 250 px and folder names are ellipsized to the available tree width.
7. Library HARDWARE suppresses partially visible columns so horizontally scrolled names cannot draw across panel boundaries.
8. SONG preset rows support drag/drop directly onto SONG arrangement slots.
9. PLAY/STOP reverse hardware behavior remains unproven: editor still sends confirmed MIDI realtime FA/FC, but user hardware test reported one-way behavior; no speculative extra command was added.
10. Full v1.58 regression, v1.59 working regression, v1.60 working regression, compileall and all-page redraw smoke pass in software/headless testing.

## v1.61 UI / sequencer pass — 2026-09-11
1. Added fixed UI SCALE presets: 50%, 100%, 125%, 150%; free window resizing is disabled.
2. Top-bar RANDOM / preset selector / INIT are contextual: SYNTH keeps the existing synth algorithms; ARP + SEQUENCER routes RANDOM to the sequencer and INIT to confirmed sequence initialization. These controls are hidden on SONG / LIBRARY / SETTINGS.
3. SEQ removes duplicate CLEAR / COPY / PASTE / RANDOM controls and unsupported RESOLUTION / STRAIGHT / TRIPLET / DOTTED controls. FILL is centered and widened with a short 64-step description. STEPS shows a muted numeric value above the fader.
4. Sequence INIT confirmation is English: Initialize sequence? YES / NO.
5. Envelope marker animation uses a visual-only perceptual minimum duration; actual ADSR parameter timing is unchanged.
6. Synth modulation depth overlay now shows Matrix Amount from a neutral zero point. Hovering the blue line for 400 ms shows source + signed Amount.
7. LIBRARY HARDWARE supports horizontal mouse-wheel scrolling and Left/Right horizontal keyboard navigation without sending Program Change for the scroll action.
8. SONG folder tree root stays visible/open, child folders remain closed until toggled, long trees can wheel-scroll, and drop-to-slot assignment has a robust metadata fallback.
9. PLAY/STOP editor -> UNO, complete 64-step hardware sequence read, and unknown SEQ/REC hardware commands remain unresolved and are not marked fixed.

## v1.62 — 2026-09-12
- UI design base corrected to 1600×900.
- UI SCALE presets corrected to 16:9: 50% 800×450; 75% 1200×675; 100% 1600×900; 125% 2000×1125; 150% 2400×1350.
- 75% scale option added.
- Default/startup geometry changed to 1600×900.
- Cumulative build includes read-only hardware sequencer 0x29 integration; STORE remains locked.

## v1.63 — 2026-09-12
1. UI SCALE reduced to 100%=1200×675, 125%=1440×810, 150%=1600×900, plus FULLSCREEN; 50%/75% removed.
2. SEQUENCER source-status caption removed from the visible header.
3. FILL gives visible pressed feedback.
4. Automation editor no longer creates four values of the same parameter inside one step; each lane/parameter has one value per step, while different parameters may coexist on that step.
5. Library selection is lightweight: click/arrows highlight only; Enter loads/previews. Top-bar preset selection is unchanged.
6. Library keyboard navigation is truly 2D across the displayed columns.
7. Library layout changed to three LOCAL columns and two right-panel columns, with a wider gap and explicit right inner frame.
8. LOCAL ALL metadata is cached per list build to remove repeated metadata reads during sort/filter/draw.
9. SONG explorer highlights preset files only, not folders.
10. 0x29 hardware read now includes selected preset bank/program bytes to address the user-reported preset-001-for-all-slots defect; non-001 addressing awaits direct hardware confirmation.
11. STORE/0x28 remains locked.

---

# v1.64 ADDENDUM — 2026-09-12

## v1.64 — 2026-09-12
- Restored 1600×1000 internal design base; fixed v1.63 vertical clipping regression.
- Scale presets: 1200×675 / 1440×810 / 1600×900; immediate application; Windows maximize restored.
- Top-bar scale icon `⛶`; removed UI Scale from Settings.
- Settings cleanup and ABOUT panel.
- Reordered LIBRARY before SONG.
- Library horizontal keyboard navigation now scrolls viewport to keep selection visible.
- Kept Enter-only load/preview behavior in Library.
- Hardware 0x29 response parsing accepts selected bank/program instead of only preset 001.
- Added MIDI Clock F8 output for software sequencer PLAY (24 PPQN).
- Rearranged oscillator/noise containers and consolidated oscillator/noise level faders.
- Reworked borderless 3-octave keyboard, octave arrows, PB Range selector, Pitch/Mod controls.
- Added automation scale labels.
- Themed internal text/info/error/confirmation dialogs; Windows file picker remains the native OS picker.
- STORE remains locked.

## v1.64 FIX — 2026-09-12
- Fixed scale popup position: menu now opens under the `⛶` button using the scaled canvas coordinates.
- Fixed keyboard-open scaling regression: keyboard adds vertical window space instead of forcing the full UI to shrink.
- Keyboard: straight top edges, lower-corner rounding only; improved polygon rendering.
- Pitch Bend uses a filled animated strip matching MOD styling.
- OSC1 vertical fader spacing aligned with OSC2/OSC3.
- FILTER/LFO label clearance corrected.
- LFO RATE/FADE IN vertical fader lengths restored.
- STORE remains locked.

## v1.64 FIX2
- Restored mathematically correct 16:10 scaling around the 1600x1000 design field: 1200x750 / 1440x900 / 1600x1000.
- Disabled arbitrary edge/corner window resizing.
- Added keyboard octave-state indicator.
- Replaced bright sequencer play column with a subtle vertical line.
- Added load-time piano-roll note-range auto-positioning and offscreen-note markers.
- MIDI CLOCK simplified to Off / MIDI MASTER; CV removed from editor clock output.
- Improved vertical-fader label clearance and LFO endpoint consistency.
