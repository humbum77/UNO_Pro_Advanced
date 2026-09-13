# FILE_FORMATS_PATHS.md

Root: actual Windows user Documents known folder / IK Multimedia / UNO Synth Pro. Presets: `*.unosyp` in preset root. Songs: `songs\*.unosong`. LIBRARY manages presets; SONG loads songs only through LOAD SONG; LIVE lists songs only. Local editor JSON `.unosyp` supports editor state roundtrip; official opaque binary `.unosyp` remains binary-safe and is not semantically rewritten.
