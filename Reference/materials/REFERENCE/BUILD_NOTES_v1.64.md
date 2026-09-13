# Build Notes v1.64

Built from v1.63 cumulatively. No permanent STORE implementation was added.

Validation performed before packaging:
- Python compile checks for all runtime modules.
- 0x29 request address tests for slots 1,2,128,129,256.
- Dynamic 0x29 response slot parser synthetic tests.
- Real preset-001 0x29 capture decode regression test.
- Static check that command 0x28 remains marked LOCKED.

Hardware-dependent behavior (preset 2+ 0x29 and MIDI Clock interaction with UNO) remains explicitly pending device verification.
