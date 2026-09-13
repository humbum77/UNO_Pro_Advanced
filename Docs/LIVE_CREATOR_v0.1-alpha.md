# Live Creator v0.1-alpha

Standalone offline alpha. Requires Python 3.10+ with Tkinter (standard Windows
Python installer). No third-party packages. Start `run_live_creator.bat`,
`python run_live_creator.py`, or `python -m live_creator`.

LIVE contains SONG CREATOR above a virtual 8×8 Performance Grid. Enter a mock
preset name and Append, or drag the preset chip into the timeline. Drop near a
block boundary inserts; drop inside replaces while retaining length. New blocks
have length 1. Select a block and use Resize or drag its right edge. Move arrows
or horizontal drag move the block and all successors, creating/shrinking EMPTY
before it. Moving left cannot cross a preceding preset. An operation exceeding
64 steps is rejected without changing the arrangement.

Click a timeline step or active grid pad to select it. The selected pad and all
steps belonging to its block are highlighted. Unused pads are disabled. EMPTY
is a slim gap with a computed range. Selection has no playback side effects.

Example: append Bass01, resize to 3; append Bass02, resize to 2. Ranges are
01-03 and 04-05. Move Bass02 right twice: EMPTY 04-05, Bass02 06-07. Resize
Bass01 to 4: subsequent ranges shift by one. Move Bass02 left to shrink the gap.

Not implemented: MIDI/SysEx, UNO adapter, Launchpad, audio/preset preview,
playback/playhead, file import, saving/embedded presets/.unosong. Names are
mock labels only; arrangements are held in memory and disappear on exit.
COPY/PASTE and STORE are absent. No HARDWARE PASS claimed.

Core: `live_creator/core/arrangement.py`. UI: `live_creator/ui/app.py`.
Tests: `python -m unittest discover -s tests -p test_live_creator.py -v`.
Release is a source distribution, not a standalone Windows EXE.
