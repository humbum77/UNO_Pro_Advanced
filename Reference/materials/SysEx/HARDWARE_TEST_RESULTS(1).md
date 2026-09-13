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
