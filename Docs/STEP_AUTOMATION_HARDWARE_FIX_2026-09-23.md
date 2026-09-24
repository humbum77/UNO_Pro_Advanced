# Step Automation hardware integration — 2026-09-23

## Controlled order addendum — 2026-09-24

The controlled DRIVE/DELAY pair closes one ambiguity in the ordered value
stream. `DELAY=31 -> DRIVE=32` and `DRIVE=32 -> DELAY=31` produce different
alignment/control bytes (`C8` and `C0`) but the same native payload `20 1F`.
The value order is canonical (`DRIVE`, then `DELAY`), not knob-recording order;
both signatures now decode to the same two lane values.

The codec now includes inverse continuous `pack7` and a native page-extension
round-trip primitive. A 450-file corpus rebuilt byte-for-byte with zero
mismatches. This is the binary writer foundation; arbitrary unknown target
selection generation and hardware STORE remain PARTIAL.

## Result

UNO Pro Advanced now uses one read-only Step Automation decoder for both factory `.unosyp` files and hardware SysEx `0x29` sequence pages. The hardware adapter passes all four page payloads to `uno_step_automation_decoder.decode_page_payloads()`; it does not maintain a second target resolver.

The defect in the superseded `CANONICAL-STEP-DECODER` build was downstream of decoding: `hardware_seq_0x29.apply_to_sequence()` copied notes, Gate, Accent and Tie but did not copy decoded Step Automation into `Sequence.automation`. The adapter now calls the shared `native_automation.apply_decoded_to_sequence()` path.

## Confirmed behavior

- Hardware maximum: 18 automation entries per step.
- Page 1 records use `Step | Count | ceil(Count / 8) selection bytes | values`.
- Factory multi-step pages are cumulative.
- Exact controlled profiles expose parameter name, native width and value.
- Unknown or ambiguous combinations retain raw records without invented parameter names.
- No Step Automation write path is claimed.

## Factory preset regression

The supplied factory preset `[053] FAKE 808` is mandatory. Its validated `CUTOFF 1` lane contains points on steps 6, 7, 11, 23, 27, 54, 55 and 59. The first values are 511, 512 and 511.

The same points must be visible after local-file loading and the complete hardware path `0x29 pages → decoder → Sequence.automation → editor lane`.

## Verification status

- Focused decoder/hardware regression in the build workspace: 19/19 PASS.
- Clean Git checkout module: 10 tests run; 6 PASS and 4 fixture-dependent SKIP when the private capture corpus is absent.
- This is SOFTWARE PASS against real captured bytes, not a new physical-device HARDWARE PASS.
- UI geometry, preset writer, STORE transaction and hardware write path were not changed.

## Release artifact

Corrected artifact: `UNO_Pro_Advanced_v0.9.7-beta2-HARDWARE-AUTOMATION-FIX.zip`.

SHA-256: `3e79c1c36908263b135fca2cd83af70f754d0cec4b6c978ed35cd7abd2149e5c`.

The earlier `CANONICAL-STEP-DECODER` artifact is invalid and must not be used.
