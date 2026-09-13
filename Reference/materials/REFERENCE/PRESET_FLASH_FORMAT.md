# PRESET_FLASH_FORMAT.md

Known research state: factory preset slots are 4096 bytes; studied preset1 starts at 0x09F000. Sequencer block is 64 records x 10 bytes at 0x101–0x380 within a slot. Exact +0 flags and per-note extra semantics are not confirmed. ENV candidates and 0x381–0x3A1 metadata remain research.

Do not equate 309-byte current-state offsets with flash step offsets. See raw archive for evidence.


## Factory bank details confirmed from embedded updater — 2026-09-10
1. Preset DfuSe target base: `0x09D000`; payload size `0x163000`.
2. Factory slot 1 starts at `0x09F000`; slot stride is `0x1000` (4096 bytes); 128 factory slots are populated.
3. Sequence area inside each slot is `0x101..0x380` inclusive = 640 bytes = 64 × 10-byte step records.
4. Per-step record: control raw, then three `[note, velocity, extra]` voice triplets. Note `0xFF` means unused voice. Control and Extra semantics remain unresolved.
5. Sequence/ARP metadata candidate range is `0x381..0x3A1` (33 bytes).
6. Factory slot59 (`DAFT FUNK`) provides a cross-check for Mod Matrix state decoding. Its first four logical routes are Destination/Source/Amount: `27/1/14`, `41/2/31`, `32/17/10`, `29/0/18`.
