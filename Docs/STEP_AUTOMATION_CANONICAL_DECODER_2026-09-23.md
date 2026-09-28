# Step Automation canonical decoder — 2026-09-23

## Scope

Implemented one read-only Step Automation decoder for both factory `.unosyp`
files and hardware 0x29 sequence pages. Hardware is an adapter: it passes the
four complete page payloads to `uno_step_automation_decoder.decode_page_payloads`.
It does not contain an independent target resolver.

## Confirmed limits and grammar

- Four sequence pages, each with a 192-byte core and optional packed extension.
- Page 1 logical extension begins with `Step`, `Count`, and
  `ceil(Count / 8)` metadata bytes.
- Pages 2–4 mirror the ordered native value stream for the controlled
  single-step captures.
- Hardware maximum: 18 automation entries per step.
- Unknown target combinations remain raw and unresolved. The decoder does not
  invent parameter IDs.

## Controlled catalogue

The exact catalogue now includes:

- 23 SINGLE targets;
- 22 adjacent pairs;
- 7 non-duplicate GAP pairs;
- MASTER_7;
- MASTER and confirmed drop profiles;
- SET_03, SET_04, and the actual three-WAVE content saved as SET_05;
- the independently validated factory multi-step CUTOFF1 layout.

Exact profiles expose parameter name, native width, raw value, unsigned value,
and signed value where applicable. Ambiguous exact signatures expose candidate
profiles but do not claim a target name.

## Verification

- Python compile pass.
- Step Automation integration: 9/9 pass.
- STORE/UI guard tests: 15/15 pass.
- Direct hardware-page parity check: WAVE3_TUNE3 resolves identically through
  `.unosyp` and 0x29 page adapters.
- Full discovery: 78 pass; four unrelated pre-existing failures remain
  (missing Git history for a safety comparison, theme swap, and two historical
  timeline geometry expectations).

No UI geometry, controls, preset writer, STORE command, or hardware write path
was changed.
