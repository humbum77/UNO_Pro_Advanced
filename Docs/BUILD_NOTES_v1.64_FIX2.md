# UNO Pro Advanced v1.64 FIX2

Cumulative build based on v1.64 FIX.

## GUI scaling
- Preserved the real design field: 1600 x 1000 (16:10).
- Window presets now preserve that ratio exactly:
  - 100% = 1200 x 750
  - 125% = 1440 x 900
  - 150% = 1600 x 1000
- Arbitrary mouse resizing from window edges/corners is disabled.
- Opening the drop-down keyboard adds vertical room instead of shrinking the 1600 x 1000 main design.

## Keyboard
- Existing three-octave keyboard geometry retained.
- Added current octave-shift number immediately to the right of the stacked octave arrows.

## Piano roll
- Bright moving column overlay replaced by a thin low-contrast vertical playhead line.
- On sequence load only, the vertical note viewport is positioned automatically.
- If all notes fit, a small margin is kept around them.
- If notes are spread across distant octaves, the 22-semitone window containing the most note events is selected; ties prefer the note median.
- Subtle up/down markers indicate notes outside the visible vertical range.
- Manual note editing does not trigger auto-positioning.

## MIDI Clock settings
- Removed CV Sync from the editor's MIDI CLOCK selector.
- MIDI CLOCK now offers only Off / MIDI MASTER.
- Existing saved MIDI value migrates to MIDI MASTER; obsolete values fall back to Off.
- Hardware UNO SYNC source settings remain a separate setting.

## Vertical faders
- Increased horizontal clearance between rotated labels and fader tracks.
- LFO RATE and FADE IN use the same top/bottom geometry with a slightly larger lower margin.

## Hardware / protocol
- No new unconfirmed SysEx mappings added.
- Hardware STORE remains locked.
- SEQ ON/OFF hardware command remains unresolved; USB MIDI Clock + PLAY/STOP are hardware-confirmed working in current testing.
- Preset #2 0x29 sequence-read anomaly remains unresolved.
