# 0x37 CURRENT STATE MAP — v1.52

Source: real UNO Synth Pro Full State Mapper v1.3 HOTFIX, 2026-09-09.

## Confirmed transport
Request: `F0 00 21 1A 02 03 37 00 00 F7`
Response: 309-byte SysEx beginning `F0 00 21 1A 02 03 00 37 00 00`.

## Sweep result
87 known preset CC controllers were swept through CC 0..127. 83 produced observable `0x37` state changes in the sequential scan. Four did not in that context: CC7, CC110, CC111, CC112.

The mapped fields often share serialized bytes, but the observed per-control bit masks are disjoint: no two mapped controls claim the same bit in this sweep. This supports dense bit packing rather than one-parameter-per-byte storage.

## Runtime safety rule
The v1.52 runtime decoder uses exact signatures from the hardware sweep only. It does not choose a nearest signature and does not invent a value for an unseen state. This matters because factory/hardware editing may expose higher-resolution or mode-dependent states not reachable in the single CC sweep.

## Sequential-scan caveat
The mapper intentionally retained raw 309-byte states, but it did not reload the preset before every parameter. Later tests therefore occurred with earlier controls left at their final value. This is especially relevant to mode-dependent Delay and Reverb parameters. Treat exact observed bit ownership as strong evidence, while treating exhaustive semantic ranges as pending until real-preset regression confirms them.

## Filter-2 label note
The standalone mapper's descriptive names around CC37..41 are not authoritative protocol names. The editor keeps its existing hardware-tested/reference mapping (`CC37 F2_MODE`, `CC38 F2_ENV`, `CC39 F2_TRACK`, `CC40 FILTER_SPACING`, `CC41 FILTER_LINK`). The sweep itself is consistent with enum-like behavior at CC37 and three-state link behavior at CC41.
