# VALIDATION v1.58 — 2026-09-10

1. Baseline reconciliation: accepted `UNO_Pro_Advanced_v1.57.zip` compared with the post-v1.57 working source. Intended deltas are limited to `.unosyp` state decode, ARP/Matrix/Voice read-side work, sequence-provenance safety, protocol-map wording, tests and documentation.
2. Python compileall: PASS.
3. `.unosyp` state roundtrip test2/test3/test4/test5: 297 file bytes -> 260 raw bytes -> 298 packed bytes -> synthetic 309-byte `0x37` -> identical 260 raw bytes: PASS.
4. Exact state LUT on all four fixtures: 82 resolved + 1 unresolved field each: PASS.
5. Sequence regression: test2, test3, test4 1081-byte files decode expected notes/velocities/extras: PASS. test5 1084-byte file is state-only and sequence decode remains disabled: PASS.
6. Headless LOCAL binary load: representative synth state, Voice read-side candidate, ARP Direction/Range/Pattern and Matrix Source/Destination paths apply to GUI model: PASS.
7. Mod Matrix slot59 cross-boundary regression reproduces four known routes exactly: PASS. Matrix Fade raw is not applied to GUI `MFADE`: PASS.
8. ARP: `0x3E` Direction/Range/Pattern receive, `0x3C 00 02` Pattern send, Range native 1..4: PASS in software/headless tests. ARP ON/OFF remains unmapped.
9. Hardware sequence safety: selecting a different hardware preset clears stale LOCAL sequence, marks origin `HARDWARE_STATE_ONLY`, and sequencer page/status explicitly state that 64 steps were not read: PASS headlessly.
10. `0x37` receive no-MIDI-echo check: PASS.
11. Main pages SYNTH / ARP + SEQUENCER / SONG / LIBRARY / SETTINGS headless redraw: PASS.
12. STORE/DEPLOY static audit: runtime contains no `0x28` SysEx constructor; lock remains active: PASS.
13. `0x36` remains TEST / NOT HARDWARE-CONFIRMED; no promotion to safe protocol is claimed.
14. Hardware validation on the real UNO Synth Pro: NOT PERFORMED by this validation.
15. Remaining protocol gaps: full 64-step hardware sequence read, Matrix Fade In semantic scale, controlled hardware differential for Voice Mode.
