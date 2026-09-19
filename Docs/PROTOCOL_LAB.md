# UNO Synth Pro Protocol Lab v0.1

Status: **RESEARCH / READ ONLY**.

Purpose: capture and classify live UNO Synth Pro MIDI/SysEx traffic without adding guessed commands to the main editor. First target is the still-unknown device/editor synchronization for **SEQ ON/OFF** and **REC ON/OFF**, especially with UNO clock source set to Internal.

## Safety boundary

v0.1 has **no MIDI output path**. It cannot send STORE `0x28`, bootloader SysEx, `0x36`, guessed SEQ/REC commands, or any other SysEx. It only listens to a selected MIDI input and supports offline HEX-log import.

Known command labels are annotations only. Unknown command IDs remain `UNKNOWN`.

## Evidence used

Project-confirmed protocol facts remain authoritative:
- IK header: `F0 00 21 1A 02 03 ... F7`.
- `0x24`: preset name/info read family.
- `0x28`: bulk preset write/STORE workflow; **LOCKED**.
- `0x29`: preset/sequence page read.
- `0x32`: current preset notification.
- `0x33`: preset select/load.
- `0x37`: current-state read.
- `0x3E`: observed ARP live state.
- `0x3C`: observed Editor→UNO ARP pattern write.
- `0x36`: external/reverse-engineering current-buffer-load candidate; still **UNVERIFIED** in this project.

The public `mungewell/uno-synth-utils` project for the original UNO Synth was reviewed only as comparative research. Its parameter IDs/format are **not promoted to UNO Synth Pro facts**.

## Workflow for SEQ/REC discovery

1. Start `ProtocolLab/protocol_lab.py`.
2. Select the UNO MIDI input and Connect.
3. Mark `BASELINE`; do nothing on the synth for a few seconds.
4. Mark `SEQ_ON`; physically switch SEQ on.
5. Mark `SEQ_OFF`; physically switch SEQ off.
6. Repeat with `REC_ON` and `REC_OFF`.
7. Export JSON/CSV and use **Compare labels**.

If physical panel changes emit SysEx, command-count and payload differences become visible without sending anything back to the device. If no SysEx is emitted, the next experiment should capture traffic while the official IK Editor is connected; that is a separate hardware test and does not justify guessing a command.

## Requirements

Python 3.10+, Tkinter, and `mido` plus a working MIDI backend for live capture. Offline HEX import works without mido.

Run parser tests:

```
python -m unittest tests.test_protocol_lab
```
