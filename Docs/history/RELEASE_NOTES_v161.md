# UNO Pro Advanced v1.61

1. Fixed UI scale presets: 50% = 640×360, 100% = 1280×720, 125% = 1600×900, 150% = 1920×1080. Manual resize is disabled.
2. SYNTH keeps the existing RANDOM and INIT behavior. On ARP + SEQUENCER the same top-bar buttons route to sequencer RANDOM and sequence INIT. SONG / LIBRARY / SETTINGS hide RANDOM, preset selector and INIT.
3. SEQ UI cleanup: duplicate CLEAR / COPY / PASTE / RANDOM removed; unsupported RESOLUTION / STRAIGHT / TRIPLET / DOTTED removed; FILL widened and centered; STEPS numeric value added.
4. Sequence INIT uses an English YES / NO confirmation dialog.
5. Envelope marker animation gains visual perceptual timing without changing actual ADSR values.
6. Modulation Amount is shown as a blue line from modulation zero; delayed hover tooltip shows source and signed Amount.
7. LIBRARY HARDWARE adds Left/Right horizontal navigation and horizontal mouse-wheel scrolling.
8. SONG tree root remains open, child folders toggle closed/open, long trees scroll, and drop-to-slot assignment was hardened.
9. Unresolved hardware research remains open: editor -> UNO PLAY/STOP, complete 64-step hardware sequence read, and unidentified SEQ/REC commands.
