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


## v1.55 — LOCAL binary preview test (2026-09-10)
- TEST/NOT YET HARDWARE-CONFIRMED: official UNO Synth Pro binary `.unosyp` matching header `25 01 00 00` and expected payload length may be previewed using externally documented current-buffer SysEx `0x36`; no Program Change, STORE or `0x28` is sent.
- After `0x36`, editor requests current state `0x37` so confirmed decoder fields can rebuild GUI from the UNO response.
- SAFETY: malformed/unexpected binary files are rejected rather than transmitted. This `0x36` path must remain TEST until reproduced on the user's real UNO.
- UI: preset context menu Favorite star is always yellow; seven smaller anti-aliased circular tags are shown directly in one row. Library tag dots use anti-aliased rendering.
