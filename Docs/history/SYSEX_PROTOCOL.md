# SYSEX_PROTOCOL.md

CONFIRMED: current-state read family includes 0x37 and returns 309-byte state captures in studied cases. Bootloader SysEx is documented in raw research and must never be sent during normal editor testing.

CAPTURE-CONFIRMED ROLE / WRITE STILL LOCKED: `0x28` appears in the real STORE workflow as a 304-byte Editor→UNO bulk preset-state write. Its serialized state body matches the `0x37` representation almost completely, but it is not a full sequence read and no runtime writer is enabled. `0x36` remains an external/reverse-engineering current-buffer-load candidate and is not hardware-confirmed in this project.

See `UNO_TEST_DATA_ALL.md` for captures/evidence.

## Preset catalog/name read — CONFIRMED 2026-09-08
Request slot N (1..256): `F0 00 21 1A 02 03 24 01 <bank> <program> F7`, where zero-based slot is split as `<bank>=n//128`, `<program>=n%128`. Real responses are 43 bytes and carry command byte `0x24` plus ASCII preset name. This is now safe for read-only hardware catalog acquisition.

## Hardware preset-change sync — CONFIRMED 2026-09-08
Real UNO change: Program Change -> `0x32` notification -> official Editor `0x37` read -> 309-byte state response -> ~0.5 s -> `0x24` name read. Custom editor may mirror these read-only requests. Exact full semantic decoding of every field in the 309-byte state packet is still incomplete; only confirmed fields may be applied.


## 0x37 current-state decode update — 2026-09-09
Transport remains confirmed: request `F0 00 21 1A 02 03 37 00 00 F7`, 309-byte response beginning `F0 00 21 1A 02 03 00 37 00 00`.

The full hardware sweep established observable bit masks for 83 known preset CC controls. v1.52 does not infer a generic serializer yet; it uses exact signatures observed during the sweep. If a factory/current state contains a signature not present in the sweep, that field is skipped instead of approximated. This is intentional because hardware knob resolution and mode-dependent fields may expose states not reachable in one MIDI-CC sweep.

Do not treat CC7/CC110/CC111/CC112 no-change results as proof that those controls are not stored. Their mapping remains PENDING.


## `.unosyp` / `0x37` state equivalence — 2026-09-10
1. `.unosyp` byte 0 is raw state byte 0.
2. `.unosyp` bytes 1..296 are 296 seven-bit values = 2072 bits = exactly 259 raw bytes.
3. Prepending file byte 0 yields the same 260-byte raw state represented by a 309-byte `0x37` reply.
4. `0x37` packs those 260 bytes with six leading pad bits into 298 seven-bit payload bytes.
5. This equivalence is used read-only to decode LOCAL binary presets through the existing exact-observed state LUT.

## ARP live SysEx — 2026-09-10
1. UNO→Editor `0x3E 00 00 <value>`: Direction values 0..9.
2. UNO→Editor `0x3E 00 01 <value>`: Range values 1..4.
3. UNO→Editor `0x3E 00 02 <3-byte mask>`: 16-step Pattern.
4. Editor→UNO Pattern: `F0 00 21 1A 02 03 3C 00 02 <mask0> <mask1> <mask2> F7`.
5. ARP ON/OFF command remains unknown; do not infer one.

## Hardware-sequence boundary
Existing captures contain no large UNO→Editor response carrying all 64 sequencer steps. The only large hardware reply observed is the 309-byte `0x37` current state. Therefore Program Change/`0x32` -> `0x37` -> `0x24` is not sufficient to construct a complete hardware preset cache with sequence.

## 0x29 normal-mode preset/sequence read — 2026-09-12
Observed official Editor request for preset 001 pages 0..4:
`F0 00 21 1A 02 03 29 00 00 <page> F7`.
Responses carry page 0 = 293 payload bytes; pages 1..4 = 192 payload bytes each.
The four sequence pages contain 182 packed bytes + 10 metadata bytes. The decoder recovers 636/640 raw sequence bytes exactly against the DFU read; only the first control byte of each 160-byte page (steps 1/17/33/49) is unavailable in the packed stream. Note/velocity/extra data is 576/576 exact and the other 60 control bytes are exact.
User hardware testing of the first integration showed that hard-coding address bytes `00 00` causes preset 001 sequence data to be read for every selected slot. v1.63 therefore constructs `<bank> <program>` from selected slot using the same 7-bit split as preset addressing (`slot-1`, //128, %128). This correction is evidence-driven by the observed defect but non-001 0x29 requests still need direct capture/hardware confirmation.

---

# v1.64 ADDENDUM — 2026-09-12

## 0x29 hardware preset/page read
Observed official request pattern:
`F0 00 21 1A 02 03 29 <bank> <program> <page> F7`

Preset address uses zero-based 7-bit bank/program in the current implementation:
- preset 1: 00 00
- preset 128: 00 7F
- preset 129: 01 00
- preset 256: 01 7F

Observed response shape:
`F0 00 21 1A 02 03 00 29 <bank> <program> <page> <payload> F7`

Payload sizes from official Editor capture:
- page 0: 293 bytes
- pages 1..4: 192 bytes each

Sequence page: 182 packed bytes + 10 metadata bytes. 636/640 raw sequence bytes are recoverable exactly versus DFU preset-1 capture. The unrecovered bytes are the first control byte of steps 1/17/33/49. Notes/velocities/extras are fully recovered.

v1.64 parser accepts dynamic bank/program and validates it against the requested hardware slot. Hardware confirmation for presets >1 is still required.

## Other commands
- 0x24 preset name/info
- 0x28 bulk preset write/store — LOCKED
- 0x32 current preset notification
- 0x33 preset select/load
- 0x37 current state read
