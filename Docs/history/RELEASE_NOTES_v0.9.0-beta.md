# UNO Pro Advanced v0.9.0-beta

Build date: 2026-09-12. Cumulative transition: legacy v1.64 FIX2 → v0.9.0-beta.
The current project's full FIX2 snapshot is the source of truth. Archived/reference builds are unchanged.

## Changes
- Removed window size presets, legacy ui_scale setting and the topbar ⛶ button. Free edge/corner resizing is enabled. The 1600 × 1000 design field and proportional canvas fitting remain; the keyboard can add vertical room.
- All vertical faders share label placement and track geometry. Side labels are centered beside the track with a fixed gap; FILTER pairs and each LFO RATE/FADE IN pair share endpoints. Control ranges and MIDI mapping are unchanged.
- LIVE song-list dragging now displays the real filename and destination outline and uses the existing select-song/assign-cell operation. SONG arrangement drag remains a preset assignment.
- Sequencer FILL is compact, with SAVE and SAVE AS alongside. The actual FIX2 element below FILL was explanatory text, not a MANUAL button. This hint is now in QUICK GUIDE.
- SAVE AS chooses a project folder and filename. Further Save As dialogs start in that folder; each new copy becomes the current working file. No automatic section subfolders are created.
- SAVE writes the current editor file, or opens Save As for a new/official-binary/hardware preset. Overwrites require confirmation. Writes are atomic. Existing official binary presets cannot be overwritten with editor JSON.
- Sound parameters and the full sequence are saved together. Dirty state detects changes and reversions in parameters, steps, automation and sequence settings. Preset switches, INIT and closing use Save / Don't Save / Cancel. Save cancellation/failure cancels the switch. Switching tabs does not discard data and does not prompt.
- Late hardware sequence/state replies cannot replace dirty working data. Loading a local part cancels pending hardware refresh jobs.
- Local roundtrips preserve FIX2 sequence metadata, including unconfirmed length and page metadata.

## Preserved / known limitations
- FIX2 thin playhead, load-only piano-roll autofit and keyboard octave indicator.
- MIDI CLOCK Off / MIDI MASTER. USB clock and PLAY/STOP retain the existing implementation.
- SEQ ON/OFF has no confirmed official command; no new command was added.
- Preset 2 0x29 anomaly remains unresolved. STORE and DEPLOY permanent writes remain locked.
- New editor-created presets use the editor JSON document. A loaded official
  binary `.unosyp` remains binary on `SAVE` / `SAVE AS`; resolved native Step
  Automation values are written without changing its target set. Hardware
  STORE remains a separate locked operation.
- Python 3.12+ and Pillow; Windows for WinMM MIDI.

## Validation
See VALIDATION_v0.9.0-beta.md and test_beta.py. Old version-specific tests remain historical references: some require private captures or obsolete UI presets and are not the current release gate.
