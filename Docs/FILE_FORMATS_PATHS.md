Current: **v0.9.2-beta**. [Requested rollback](RELEASE_NOTES_v0.9.2-beta.md) supersedes the historical notes below.

# Current release: v0.9.0-beta

The post-FIX2 changes are implemented in this build. See [release notes](RELEASE_NOTES_v0.9.0-beta.md) and [validation](VALIDATION_v0.9.0-beta.md) for current status. Earlier statements below are historical and are superseded by these release notes where they differ. Hardware limitations remain open.

---

# FILE_FORMATS_PATHS.md

Root: actual Windows user Documents known folder / IK Multimedia / UNO Synth Pro. Presets: `*.unosyp` in preset root. Songs: `songs\*.unosong`. LIBRARY manages presets; SONG loads songs only through LOAD SONG; LIVE lists songs only. Local editor JSON `.unosyp` supports editor state roundtrip; official opaque binary `.unosyp` remains binary-safe and is not semantically rewritten.
