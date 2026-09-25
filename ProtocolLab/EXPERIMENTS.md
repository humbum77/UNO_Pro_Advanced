# UNO State Investigator

Source-first hardware research workflow. No guessed SEQ/REC write command is enabled.

## Modes

### MANUAL — DEVICE
Use the physical SEQ or REC button on the UNO. Capture baseline traffic/state, press
the hardware button, capture again, then repeat ON/OFF cycles. MIDI Clock F8 is
discarded. Compare unsolicited packets and stable byte/bit changes.

### AUTO
AUTO means automated capture/read/diff, not guessed device control. The utility may
issue only protocol reads already confirmed by the project (notably 0x37) and performs
repeated snapshots/diffs automatically. Until a SEQ/REC setter is hardware-confirmed,
AUTO never invents or transmits one.

## Evidence promotion
A candidate offset/mask or command stays CANDIDATE until it repeats across multiple
physical transitions. Promote to CONFIRMED only after hardware evidence is saved.
