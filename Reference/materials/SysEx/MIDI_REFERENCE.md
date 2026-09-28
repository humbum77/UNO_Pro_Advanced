# MIDI_REFERENCE.md

Authoritative quick reference for currently relevant verified mappings.

## CONFIRMED / official
- LFO1 Fade In CC46; LFO2 Fade In CC50.
- Filter1 mode CC30 raw: 0/25/50/75/100.
- Filter2 mode CC37 raw: 0/20/40/60/80/100.
- Mod type CC95 raw: 0/42/84.
- Delay type CC100 raw: 0/25/50/75/100.
- Reverb type CC107 raw: 0/32/64/96.
- Current-state 309-byte sequencer fields: Direction byte219 mask0x30; Gate bytes220/221; Tie byte220 mask0x10; Accent byte223.

## NOT CONFIRMED
- Hardware write command for per-step Gate/Tie/Accent/Length.
- Bulk STORE payload semantics (`0x28`).
- Exact official binary `.unosyp` semantic mapping.

Full evidence/raw captures are in `UNO_TEST_DATA_ALL.md`.
