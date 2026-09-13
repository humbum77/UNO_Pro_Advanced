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

