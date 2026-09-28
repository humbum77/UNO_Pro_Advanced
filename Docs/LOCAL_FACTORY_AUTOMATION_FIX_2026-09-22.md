# Local factory automation integration fix

The local binary `.unosyp` load path now maps every resolved native automation
entry into the matching `Sequence.automation` lane before the preset reaches
the editor UI.

For the supplied factory `FAKE 808(1).unosyp` fixture, the complete
`App.load_local_preset()` path is regression-tested. It selects `CUTOFF 1` and
exposes eight decoded points on steps 6, 7, 11, 23, 27, 54, 55 and 59.

The native result records `decoded_lane_points`. A recognized profile with
entries that maps to zero editor points is treated as an error instead of
silently presenting an empty lane.

Scope: SOFTWARE PASS for this supplied factory profile and local editor load.
This does not claim universal parameter-selection decoding, native automation
writing, or a hardware pass.
