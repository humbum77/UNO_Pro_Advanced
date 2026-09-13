# v0.9.1-beta — preset browsing warning fix

2026-09-12. Cumulative from v0.9.0-beta; legacy FIX2 foundation preserved.

Fixed false unsaved-change warnings when browsing presets:
- Drawing FX controls no longer changes the saved/loaded document.
- Bank select and performance modulation wheel are excluded from dirty comparisons.
- Ancillary MIDI synth replies during the two-second preset synchronization window update the clean baseline only for fields that were not already edited. Recorded sequence changes and existing editor changes remain dirty. Hardware parameter changes outside that window still count as edits.
- Save / Don't Save / Cancel remains active for actual unsaved changes.

Validation: all 15 offline tests pass; three new regressions reproduce against v0.9.0-beta and pass against this build. All Python files compile. MIDI/protocol modules remain unchanged. No native Tk or real-device validation was performed in this environment; see prior validation for its Tk runtime limitation.

## Test output
```
test_bank_and_performance_wheel_are_not_edits (__main__.BetaTests.test_bank_and_performance_wheel_are_not_edits) ... ok
test_binary_never_overwritten (__main__.BetaTests.test_binary_never_overwritten) ... ok
test_browsing_sync_has_no_prompt (__main__.BetaTests.test_browsing_sync_has_no_prompt) ... ok
test_cancel_and_atomic_failure (__main__.BetaTests.test_cancel_and_atomic_failure) ... ok
test_cancel_switches_before_mutation (__main__.BetaTests.test_cancel_switches_before_mutation) ... ok
test_dirty_all_sequence_fields_and_revert (__main__.BetaTests.test_dirty_all_sequence_fields_and_revert) ... ok
test_late_hardware_does_not_replace_edits (__main__.BetaTests.test_late_hardware_does_not_replace_edits) ... ok
test_live_drag_assignment (__main__.BetaTests.test_live_drag_assignment) ... ok
test_pages_and_geometry (__main__.BetaTests.test_pages_and_geometry) ... ok
test_protocol_and_static (__main__.BetaTests.test_protocol_and_static) ... ok
test_protocol_note_payload (__main__.BetaTests.test_protocol_note_payload) ... ok
test_redraw_does_not_dirty_loaded_fx (__main__.BetaTests.test_redraw_does_not_dirty_loaded_fx) ... ok
test_save_as_current_and_roundtrip (__main__.BetaTests.test_save_as_current_and_roundtrip) ... ok
test_sync_keeps_local_edits_and_recorded_notes_dirty (__main__.BetaTests.test_sync_keeps_local_edits_and_recorded_notes_dirty) ... ok
test_three_way_prompt (__main__.BetaTests.test_three_way_prompt) ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.699s

OK

```
