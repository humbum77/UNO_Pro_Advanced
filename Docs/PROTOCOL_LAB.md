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


## Comparative protocol research — original UNO Synth

The public `mungewell/uno-synth-utils` research documents an original-UNO command that is directly relevant to the Pro synchronization problem:

`F0 00 21 1A 02 01 14 F7` — **CMD 0x14: Report Sequence State**.

Observed original-UNO responses use `F0 00 21 1A 02 01 00 14 ... F7`. In those captures, one status byte changes with panel state: bit `0x04` tracks SEQ LED, `0x01` PLAY, `0x02` REC (flashing), `0x08` HOLD; ARP was observed in another response byte. These are facts about the **original UNO Synth**, not yet facts about UNO Synth Pro.

Why this is a high-value Pro candidate: the product-family framing is structurally similar and two command IDs are already shared across generations in our evidence: `0x24` is used for preset read/name information and `0x33` for preset selection/load. Therefore the Pro-shaped read-only candidate is:

`F0 00 21 1A 02 03 14 F7`

Status: **CANDIDATE / PRO HARDWARE UNVERIFIED**. Protocol Lab v0.1 catalogs incoming `0x14` but does not transmit this request automatically. A real Pro response is required before any bit mapping is promoted to CONFIRMED.

## Offline .unosyp research

`ProtocolLab/unosyp_probe.py` reports the confirmed native automation container without assigning unknown semantics:

- binary Pro magic `25 01 00 00`;
- automation byte count at offset 494;
- reserved/unknown byte 495;
- raw automation payload beginning at offset 496;
- raw two-byte entry grouping.

The supplied research corpus contains binary examples with counts 0, 2, 4, 28 and 34. Example raw payloads include `29 01`, `58 0E`, and `58 0E 08 C3`. Filenames alone are not sufficient evidence to name those two-byte entries, so the probe intentionally preserves them as raw values.

This confirms the tooling can isolate candidate automation entries for differential experiments while keeping parameter identity/value/step packing PARTIAL/UNKNOWN.
