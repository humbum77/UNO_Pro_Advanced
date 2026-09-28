# PRESET_FLASH_FORMAT.md

Known research state: factory preset slots are 4096 bytes; studied preset1 starts at 0x09F000. Sequencer block is 64 records x 10 bytes at 0x101–0x380 within a slot. Exact +0 flags and per-note extra semantics are not confirmed. ENV candidates and 0x381–0x3A1 metadata remain research.

Do not equate 309-byte current-state offsets with flash step offsets. See raw archive for evidence.
