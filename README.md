# UNO Pro Advanced v0.9.7-beta

Cumulative integration of main v0.9.5-beta and Live Creator v0.6-alpha. Windows, Python 3.12+, Tkinter and Pillow. Run run_editor.bat. This is a source release, not an autonomous EXE.

[Русский](README.ru.md) · [Release notes](Docs/RELEASE_NOTES_v0.9.7-beta.md) · [Project state](Docs/PROJECT_STATE.md) · [Changelog](CHANGELOG.md)

LIVE is embedded in the main window. LENGTH, Dupl, parameter Automation selector, native raw reader and global themes are included. STORE remains locked. Native event mapping/writer and Live Creator hardware playback remain PARTIAL/UNVERIFIED. Settings/state/logs use %LOCALAPPDATA%\UnoLive; original presets remain in their user folder.

v0.9.7-beta adds the shared local `.unosyp` / hardware SysEx `0x29` sequence decoder with confirmed Gate, Accent and Tie support. The approved envelope animation and its S–R geometry are locked against changes unless the user explicitly requests them.
