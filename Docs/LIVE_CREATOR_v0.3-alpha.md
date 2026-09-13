# Live Creator v0.3-alpha

Source release, Python 3.10+ with Tkinter. Launch run_live_creator.bat.

Implements UNO_Local_Live_Creator_next_build_TASK.md from v0.2-alpha.
Full-width timeline is 86 px high (previously 130). PRESETS and WORK AREA
are both 260 px wide. A pure square 8×8 matrix occupies the centre.
UNO palette and flat control geometry use the inherited app.py reference.
Scrollbars are custom thin grey tracks with orange thumbs, dropdowns are dark,
and application buttons are custom Canvas controls. File dialogs remain native.

LOCAL PRESETS: click folders to expand; drag .unosyp to timeline. Right-click
browser → Open folder changes root. Drop at boundary inserts; drop inside
replaces and preserves length. Drag right edge resizes; drag body moves with
ripple. Overflow is rejected. EMPTY is a compressed gap. Editing stops the
software transport and clears the loop; selection follows blocks.

Click selects; Ctrl-click or Shift-click toggles blocks in shared selection
from either view. Shift-right-click sets a loop spanning selected blocks;
repeat with the same range to clear. Orange underline marks loop in timeline.
White line/outline marks playhead independently of orange selection.

PLAY starts at the selected step or at 1. With loop enabled, an out-of-range
selection starts at loop start. STOP retains the playhead. Tempo is global,
20–300 BPM. This iteration uses one beat per Song Step for software visual
transport only: no sound, UNO preset application, MIDI clock or hardware
sequence-duration claim. No hardware commands or controller mappings added.

NEW clears arrangement after unsaved-change confirmation. OPEN/SAVE use a
minimal internal .unosong ZIP with manifest and original raw .unosyp bytes,
SHA-256 IDs and deduplication. Saving is atomic; load validates IDs, size,
length and tempo before replacing current data. This is not an IK format.

Remaining placeholders: HARDWARE PRESETS shows UNO not connected; no device
adapter is wired. CREATOR/LIVE switch maintains page mode but both currently
share editing and software transport; LIVE-specific song browser and external
controller profiles are deferred. No real audio playback or HARDWARE PASS.

Checks: 19 unittest cases (existing regression + transport/loop/container),
native GUI interaction and layout smoke at 960×600/1200×750/1440×900,
compile/import, git diff --check, ZIP integrity and SHA-256 manifest.
