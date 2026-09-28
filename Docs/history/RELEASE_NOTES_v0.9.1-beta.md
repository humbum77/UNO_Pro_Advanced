# v0.9.1-beta — preset browsing warning fix

2026-09-12. Cumulative from v0.9.0-beta; legacy FIX2 foundation preserved.

Fixed false unsaved-change warnings when browsing presets:
- Drawing FX controls no longer changes the saved/loaded document.
- Bank select and performance modulation wheel are excluded from dirty comparisons.
- Ancillary MIDI synth replies during the two-second preset synchronization window update the clean baseline only for fields that were not already edited. Recorded sequence changes and existing editor changes remain dirty. Hardware parameter changes outside that window still count as edits.
- Save / Don't Save / Cancel remains active for actual unsaved changes.

Validation: all 15 offline tests pass; three new regressions reproduce against v0.9.0-beta and pass against this build. All Python files compile. MIDI/protocol modules remain unchanged. No native Tk or real-device validation was performed in this environment; see prior validation for its Tk runtime limitation.
