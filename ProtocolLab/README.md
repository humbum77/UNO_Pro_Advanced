# UNO Synth Pro Utility — Protocol Lab

Standalone Windows research utility for UNO Synth Pro.

## Start

Double-click `run_protocol_lab.bat`. The launcher installs the small MIDI runtime dependencies and opens the utility.

The current release is deliberately read-only for unknown protocol operations. It can capture and decode live SysEx, compare hardware-state experiments, import/export logs, and inspect native `.unosyp` automation containers.

## Current protocol target

The strongest state-sync candidate found in comparative research is command `0x14` ("Report Sequence State") from the original UNO Synth. The Pro-shaped request would be `F0 00 21 1A 02 03 14 F7`, but it remains hardware-unverified and is not transmitted automatically.

Use the capture labels BASELINE / SEQ_ON / SEQ_OFF / REC_ON / REC_OFF to establish the Pro mapping from real traffic before enabling any setter.

See `../Docs/PROTOCOL_LAB.md` and `../Docs/PROTOCOL_LAB_REPORT.md`.


## SEQ / REC State Investigator

The GUI includes AUTO and MANUAL — DEVICE research modes.

- MANUAL — DEVICE: press SEQ/REC physically on the UNO, request/capture confirmed 0x37 state snapshots, repeat OFF/ON cycles, then Analyze.
- AUTO: automates confirmed state-read/diff workflow only. It does not invent a SEQ/REC setter.
- MIDI Clock F8 is filtered by default; enable "Show MIDI Clock (F8)" only for clock diagnostics.
- Stable candidates are reported as byte offset + bit mask + transition. Repeat multiple OFF/ON cycles before treating a candidate as evidence.

The only transmit operation added for this investigator is the project-confirmed 0x37 current-state read. Unknown setters and 0x28 STORE remain locked.
