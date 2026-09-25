# UNO Synth Pro Protocol Lab — completion report

Date: 2026-09-19  
Branch: `research/protocol-lab`  
Scope: non-destructive protocol research and tooling for UNO Synth Pro, with priority on SEQ/REC synchronization.

## Result

Protocol Lab v0.1 is implemented as a separate research tool. It does not alter the main editor and does not guess write commands.

Implemented:
- live MIDI IN monitoring;
- SysEx capture with full HEX;
- IK Multimedia UNO Synth Pro frame recognition;
- request/notify-like vs response-like framing;
- known command annotation;
- experiment labels `BASELINE`, `SEQ_ON`, `SEQ_OFF`, `REC_ON`, `REC_OFF`;
- command-count comparison;
- same-length packet byte diff and XOR masks;
- payloads unique to the post-action capture;
- JSON/CSV export;
- offline HEX-log import;
- read-only native `.unosyp` automation-container probe;
- unit tests for parser, diff logic and `.unosyp` probe.

## High-value protocol finding

Comparative research of the original UNO Synth found a directly relevant command:

`F0 00 21 1A 02 01 14 F7` — CMD `0x14`, **Report Sequence State**.

Published original-UNO captures show a status response where:
- `0x04` tracks SEQ;
- `0x01` tracks PLAY;
- `0x02` tracks REC;
- `0x08` tracks HOLD;
- ARP is represented in another observed response byte.

UNO Synth Pro uses product byte `03`, while original UNO uses `01`. The Pro-shaped candidate is therefore:

`F0 00 21 1A 02 03 14 F7`

This is **CANDIDATE / PRO HARDWARE UNVERIFIED**, not a confirmed Pro command.

The candidate is stronger than a blind guess because command-family continuity is already independently visible: both generations use `0x24` in preset read/name workflows and `0x33` for preset selection/load. This increases the value of testing `0x14`, but does not prove it.

Protocol Lab catalogs incoming `0x14` and preserves its unverified status. It does not automatically transmit it.

## Native automation corpus result

The supplied research archive was inspected independently. Binary Pro `.unosyp` samples confirm the existing project container boundary:
- magic `25 01 00 00`;
- byte 494 is the automation payload byte count in the studied binary files;
- byte 495 is preserved as unknown/reserved;
- automation payload starts at byte 496;
- two-byte raw grouping is preserved without assigning semantics.

Observed binary research samples include automation byte counts 0, 2, 4, 28 and 34. Examples:
- `AUTO_L4.unosyp`: count 2, raw `29 01`;
- `AUTO_L5.unosyp`: count 2, raw `58 0E`;
- `AUTO_L6.unosyp`: count 4, raw `58 0E 08 C3`.

These observations support the existing reader boundary, but do **not** identify the exact parameter/value/step packing. Filenames are not treated as sufficient proof.

## Public-source cross-check

The UNO Synth Pro manual confirms that SEQ and REC are internal sequencer modes: SEQ activates/deactivates sequencer mode; REC engages step recording; realtime recording uses SEQ + REC + PLAY. The public MIDI documentation does not expose a normal CC for SEQ/REC mode switching.

The original UNO public reverse-engineering material documents `0x14 Report Sequence State`, making it the strongest currently identified lead for Pro state synchronization.

## Safety status

Still locked:
- STORE / `0x28`;
- unknown write commands;
- inferred SEQ/REC setters;
- bootloader SysEx;
- promotion of legacy UNO bit meanings to Pro without hardware evidence.

No unknown write command was added to UNO2.1.

## Validation boundary

Software implementation and static protocol research are complete for this stage.

The one result that cannot be completed without a physical UNO Synth Pro is **HARDWARE PASS** of the Pro-shaped `0x14` request and the resulting response/bit mapping. A real-device capture is required to distinguish:
1. `0x14` is retained by Pro and directly reports SEQ/REC state;
2. `0x14` exists but its payload changed;
3. Pro moved sequence state to another command.

Until that capture exists, SEQ/REC remains CANDIDATE rather than CONFIRMED.

## Files

- `ProtocolLab/protocol_lab.py`
- `ProtocolLab/unosyp_probe.py`
- `Docs/PROTOCOL_LAB.md`
- `tests/test_protocol_lab.py`
- `tests/test_unosyp_probe.py`

Main editor behavior and the locked ADSR implementation were not changed.


## State Investigator completion update

Implemented on research/protocol-lab:
- source module ProtocolLab/state_investigator.py with byte/bit differential correlation;
- GUI modes AUTO and MANUAL — DEVICE for SEQ/REC experiments;
- confirmed read-only 0x37 current-state request over MIDI OUT;
- automatic capture of the matching 0x37 response in AUTO mode;
- physical-device workflow using repeated OFF/ON snapshots;
- capture of non-SysEx raw MIDI as well as SysEx, so hardware-button notifications are not missed;
- MIDI Clock F8 filtered by default and excluded from investigator signatures;
- unit coverage for byte/bit correlation and F8 exclusion;
- Windows workflow updated to run the investigator tests.

Safety boundary remains unchanged: no guessed SEQ/REC setter, no 0x28 STORE, and no promotion of 0x14 to confirmed without UNO Synth Pro hardware evidence.

### Hardware gate

Software work can determine candidates from captures, but the actual Pro SEQ/REC state mapping requires real transitions from the physical UNO. Required evidence is repeated SEQ OFF/ON/OFF and REC OFF/ON/OFF cycles with 0x37 snapshots and unsolicited traffic saved. Only repeatable candidates should be promoted to CONFIRMED.
