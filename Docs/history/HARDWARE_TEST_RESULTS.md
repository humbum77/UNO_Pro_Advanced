# HARDWARE_TEST_RESULTS.md

Hardware-confirmed/frozen: FX type enumerations (MOD 0/42/84, DELAY 0/25/50/75/100, REVERB 0/32/64/96); 309-byte Direction/Gate/Tie/Accent fields from controlled tests.

v1.48 still requires real Windows/UNO validation for INIT safety, preset synchronization, file discovery and sequencer playback. Do not repeat already-completed Gate/Tie/Accent controlled tests unless a genuinely new differential measurement is required.

## 2026-09-08 test3 — HARDWARE preset sync (CONFIRMED)
- Real UNO preset change emits Program Change followed by SysEx `0x32` current-preset notification.
- Official Editor then requests current state with `F0 00 21 1A 02 03 37 00 00 F7`; UNO returns 309-byte `0x37` state dump.
- About 0.5 s later official Editor requests current preset name with `0x24`; UNO returns a 43-byte `0x24` response containing the slot address and ASCII name.
- Sequence repeated cleanly for slots 001, 002, 003 in `test3`.
- Example names from the capture: 001 `THE ONE`, 002 `PUNCH BASS 3`, 003 `BASS`.


## 2026-09-09 — Full State Mapper + v1.52 decoder basis
- Real UNO confirmed v1.51 hardware preset names load successfully through `0x24`.
- v1.51 still left SYNTH GUI parameters stale after hardware preset changes; therefore full state decode remained unfinished.
- Standalone MIDI Monitor v1.3 HOTFIX, using the proven Windows WinMM layer, completed the full automated state sweep.
- Sweep scope: 87 known preset CC controllers × CC values 0..127 = 11,136 control points, each followed by confirmed `0x37` read.
- Differential analysis found observable `0x37` signatures for 83 scanned CCs.
- Four entries showed no `0x37` change in that sequential scan context: CC7, CC110, CC111, CC112. This does NOT prove those parameters are absent from preset state; Reverb controls can be mode-dependent.
- Mapped controls share many bytes but their observed masks do not overlap the same bit. This strongly supports dense packed serialization.
- v1.52 uses exact observed signatures only; real-hardware preset regression is required before freezing full GUI sync.

## v1.58 real-hardware validation — user tests 2026-09-10/11
1. LOCAL `.unosyp` sequence step data: PASS. Steps change correctly for the supported 1081-byte files.
2. Synth-GUI comparison across test2/test3/test4 is NOT a valid differential test because those files contain the same Init synth sound. Do not claim GUI synth-state differences from that fixture set.
3. Velocity editing: PASS on real use; value changes and is adjustable.
4. test5 `.unosyp` 1084 safe handling: PROVISIONAL PASS. No obvious crash or invented sequence observed; keep sequence decoding unsupported for this variant.
5. Mod Matrix Source / Destination / Amount: HARDWARE PASS. Real preset changes are reflected in the GUI.
6. Voice Mode: HARDWARE FAIL. A paraphonic hardware preset still appears as LEGATO in the GUI. The current raw bits 85..86 candidate must not be considered confirmed.
7. ARP preset Direction / Range / Pattern: HARDWARE PASS; Pattern works in both directions.
8. ARP ON/OFF: MISSING SYNC. GUI enable state is not synchronized with the hardware.
9. LOCAL → HARDWARE switch clears stale local sequence: HARDWARE PASS.
10. Normal hardware preset synchronization: HARDWARE PASS.
11. MIDI echo/loop protection: PROVISIONAL PASS; longer testing still required.
12. SEQ ON/OFF: MISSING SYNC. Hardware sequencer active state can be changed from either physical SEQ or PLAY, so a single guessed toggle command/state is not sufficient.
13. Hardware 64-step sequence read: STILL UNRESOLVED. Sequence steps do not load from the hardware because no confirmed full-sequence read command is known.
14. Intermittent LOCAL/HARDWARE/LOCAL GUI synchronization stall: reproduced in v1.57; NOT REPRODUCED in repeated v1.58 tests so far. Treat as provisional improvement, not final hardware closure.
15. Matrix Fade In: USER-CONFIRMED WORKING in current use. Preserve the existing control behavior; do not treat Matrix Fade In itself as a v1.59 defect. This does not by itself prove the packed-state 10-bit read-side scaling formula, so do not invent or remap raw-state semantics without a differential decode.


## 2026-09-11 v1.59 protocol updates
1. Voice Mode receive confirmed: raw byte 175 bits 5-6 = MONO/LEGATO/PARA 0/1/2; live `0x34 04 <0..2>` updates GUI without echo.
2. ARP ON/OFF live receive confirmed: `0x34 06 01/00`; captured 0x37 dumps do not carry this live state.
3. Sequencer transport confirmed: MIDI realtime `FA` = PLAY/START, `FC` = STOP. Editor PLAY/STOP uses these messages; incoming FA/FC updates GUI.
4. Physical SEQ and REC mode buttons produced no monitor-visible command; no mapping is invented for them.

## 2026-09-12 — normal-mode 0x29 sequence read
- Official Editor `< TO LIB` capture for hardware preset 001 uses command 0x29 pages 0..4.
- Payload sizes: page0 293; pages1..4 192 each.
- Compared with the 640-byte DFU preset1 sequence block: 636/640 bytes recover exactly; missing bytes are only first control bytes at raw offsets 0,160,320,480. Notes/velocity/extra recover 576/576 exactly.
- User test of UNO Pro Advanced integration: sequence transfer/read works, but every hardware preset displayed preset 001 sequence. Root cause in our code: 0x29 requests were hard-coded to address `00 00` regardless of selected slot.
- v1.63 changes those address bytes from the selected slot. Test on non-001 hardware preset is pending.

---

# v1.64 ADDENDUM — 2026-09-12

## v1.64 pending hardware checks
1. Select presets 2+ and confirm 0x29 responses carry the corresponding bank/program and sequences populate correctly.
2. With UNO configured for external/USB MIDI sync, verify software PLAY + generated F8 clock starts/moves the hardware sequencer as expected.
3. Confirm PB Range UI semantics before adding any hardware transmission for that setting.
