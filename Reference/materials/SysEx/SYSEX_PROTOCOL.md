# SYSEX_PROTOCOL.md

CONFIRMED: current-state read family includes 0x37 and returns 309-byte state captures in studied cases. Bootloader SysEx is documented in raw research and must never be sent during normal editor testing.

STRONG/NOT CONFIRMED: 0x28 is associated with bulk preset write/store but payload transform is not sufficiently verified. STORE remains locked. Other 0x23/0x24/0x34/0x35/0x36 commands remain research items.

See `UNO_TEST_DATA_ALL.md` for captures/evidence.

## Preset catalog/name read — CONFIRMED 2026-09-08
Request slot N (1..256): `F0 00 21 1A 02 03 24 01 <bank> <program> F7`, where zero-based slot is split as `<bank>=n//128`, `<program>=n%128`. Real responses are 43 bytes and carry command byte `0x24` plus ASCII preset name. This is now safe for read-only hardware catalog acquisition.

## Hardware preset-change sync — CONFIRMED 2026-09-08
Real UNO change: Program Change -> `0x32` notification -> official Editor `0x37` read -> 309-byte state response -> ~0.5 s -> `0x24` name read. Custom editor may mirror these read-only requests. Exact full semantic decoding of every field in the 309-byte state packet is still incomplete; only confirmed fields may be applied.


## 0x37 current-state decode update — 2026-09-09
Transport remains confirmed: request `F0 00 21 1A 02 03 37 00 00 F7`, 309-byte response beginning `F0 00 21 1A 02 03 00 37 00 00`.

The full hardware sweep established observable bit masks for 83 known preset CC controls. v1.52 does not infer a generic serializer yet; it uses exact signatures observed during the sweep. If a factory/current state contains a signature not present in the sweep, that field is skipped instead of approximated. This is intentional because hardware knob resolution and mode-dependent fields may expose states not reachable in one MIDI-CC sweep.

Do not treat CC7/CC110/CC111/CC112 no-change results as proof that those controls are not stored. Their mapping remains PENDING.
