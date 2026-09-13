# Validation — v0.9.0-beta

Python 3.12: all packaged Python files compile; runtime modules import.
11 offline regression tests pass. Coverage: Save/Save As, Unicode filenames, current-file reassignment, parameter/sequence metadata roundtrip, dirty changes and reversion, cancelled switches and dialogs, overwrite refusal, atomic-write failure cleanup, binary protection, LIVE drag assignment, Canvas render/hitbox smoke tests for all pages, shared FILTER/LFO endpoints, 0x29 request/response addresses and synthetic note/velocity decoding.

Protocol and MIDI modules are byte-identical to FIX2. Thin playhead, autofit, keyboard/octave, STORE/DEPLOY locks and MIDI clock methods are AST-identical to FIX2.

Limits: native Tk window launch was attempted but the bundled environment reported "Can't find a usable init.tcl". Tests use a mocked Tk/Canvas and MIDI transport; they do not establish real-window visual quality or hardware correctness. Hardware and interactive desktop acceptance remain unperformed. No MIDI hardware was accessed during validation.

Old version-specific tests were retained as historical references, not run as current UI requirements. Private .unosyp capture files are not included in this ZIP.

## Test output
```
test_binary_never_overwritten (__main__.BetaTests.test_binary_never_overwritten) ... ok
test_cancel_and_atomic_failure (__main__.BetaTests.test_cancel_and_atomic_failure) ... ok
test_cancel_switches_before_mutation (__main__.BetaTests.test_cancel_switches_before_mutation) ... ok
test_dirty_all_sequence_fields_and_revert (__main__.BetaTests.test_dirty_all_sequence_fields_and_revert) ... ok
test_late_hardware_does_not_replace_edits (__main__.BetaTests.test_late_hardware_does_not_replace_edits) ... ok
test_live_drag_assignment (__main__.BetaTests.test_live_drag_assignment) ... ok
test_pages_and_geometry (__main__.BetaTests.test_pages_and_geometry) ... ok
test_protocol_and_static (__main__.BetaTests.test_protocol_and_static) ... ok
test_protocol_note_payload (__main__.BetaTests.test_protocol_note_payload) ... ok
test_save_as_current_and_roundtrip (__main__.BetaTests.test_save_as_current_and_roundtrip) ... ok
test_three_way_prompt (__main__.BetaTests.test_three_way_prompt) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.338s

OK

```
