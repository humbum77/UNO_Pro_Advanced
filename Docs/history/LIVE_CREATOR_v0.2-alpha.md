# Live Creator v0.2-alpha

Run `run_live_creator.bat` or `python -m live_creator`. Source distribution:
Python 3.10+ with Tkinter required. No third-party runtime packages.

1200×750 starting geometry follows UNO's 16:10 workspace. The palette is
extracted from the inherited UNO app.py. Discovery follows the inherited
storage.py Documents lookup, alphabetical folders, and exclusion of songs.
These small read-only portions are adapted separately to avoid importing
the legacy UI, storage side effects, or MIDI runtime.

LOCAL PRESETS opens the standard UNO Editor Documents folder. Use its `…`
button to choose another root. Expand folders, then drag a .unosyp to the
timeline. Drop at a boundary inserts; drop on a block replaces while retaining
duration. Drop at the end adds one step. Drag a block to move it; drag its right
edge to resize. Each 64 horizontal pixels represents one edit step. EMPTY
is compressed visually. Moving left consumes only the preceding EMPTY.
Overflows display `64-step limit reached` and leave the arrangement intact.

Timeline and grid share selection. Active pads select individual Song Steps;
unused pads do nothing. A separate Core playhead can be rendered in both views,
but no playback engine advances it in this release. The 16 extra function pads
are deliberately inactive pending an agreed mapping.

Original preset bytes are captured in memory with SHA-256 IDs. Moving or
removing a source file after a drop cannot change those captured bytes.
No preset decoding, sound preview, MIDI, SysEx, Launchpad hardware integration,
STORE, COPY/PASTE or .unosong persistence is implemented. Arrangements remain
in memory only and are lost on closing the app.

Reference for future hardware integration:
https://userguides.novationmusic.com/hc/en-gb/sections/23731330371602-Launchpad-Mini-User-Guide

The requested task filename was absent; AGENTS.md contained the full v0.2-alpha
task and was used as the specification. Existing user AGENTS.md edits preserved.

Checks: unittest discovery with test_*.py; GUI drag/drop, resize, move, selection,
inactive pads and geometry smoke; compile/import; git diff --check; ZIP integrity
and payload SHA-256 validation. All are software checks; no HARDWARE PASS.
