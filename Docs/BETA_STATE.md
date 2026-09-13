Current: **v0.9.2-beta**. [Requested rollback](RELEASE_NOTES_v0.9.2-beta.md) supersedes the historical notes below.

Current release: **v0.9.1-beta**. See [warning fix](RELEASE_NOTES_v0.9.1-beta.md). Earlier release notes below are historical.

# Current release: v0.9.0-beta

The post-FIX2 changes are implemented in this build. See [release notes](RELEASE_NOTES_v0.9.0-beta.md) and [validation](VALIDATION_v0.9.0-beta.md) for current status. Earlier statements below are historical and are superseded by these release notes where they differ. Hardware limitations remain open.

---

# UNO Pro Advanced — beta state

Current development line: **v0.9.0-beta**  
Legacy transition baseline: **v1.64 FIX2**

## Confirmed hardware status

- Normal-mode hardware preset/page read through SysEx `0x29` is integrated.
- Hardware sequences are decoded from pages 0..4; all tested presets currently work except preset #2, which remains a separate unresolved case.
- MIDI Clock over USB is heard by the UNO when the synth is configured for USB synchronization.
- PLAY / STOP work over the current MIDI transport path.
- Hardware **SEQ ON/OFF** remains unresolved and must be decoded as a separate hardware command; it is not treated as a Clock problem.
- Permanent STORE / bulk write remains locked.

## Current beta UI/workflow items

Historical planning list from before the full FIX2 synchronization follows.
Some items were already implemented in FIX2; the shipped baseline is described
in [BUILD_NOTES_v1.64_FIX2.md](BUILD_NOTES_v1.64_FIX2.md). In particular, FIX2
already includes the octave-shift display, thin playhead, note viewport positioning
and fader-spacing changes. The list below is not a list of wholly outstanding work.
See [SNAPSHOT_SYNC.md](SNAPSHOT_SYNC.md) for synchronization scope.

- Remove custom UI scale presets and the scale control; keep the current window resizing behaviour instead.
- Fix vertical-fader label geometry through a shared vertical-fader layout rather than per-block offsets.
- Restore drag visualization in LIVE mode.
- Sequencer: move MANUAL into QUICK, reduce FILL, and add Save / Save As controls.
- Sequencer project workflow: one song/project = one folder; sequence variants are separate files in that folder, without automatically generated Verse/Chorus subfolders.
- Save As keeps the project folder as the default destination and makes the new file the current working file.
- Add current-octave display next to the octave up/down controls.
- Replace the bright piano-roll playback indicator with a subtle vertical playhead line.
- After sequence load, auto-position the piano roll to the most useful/dense note range; indicate notes above/below the visible range.

## Versioning

See `VERSIONING.md`. Historical v1.x build names remain unchanged; new builds no longer use `FIX` / `FIX2` suffixes.
