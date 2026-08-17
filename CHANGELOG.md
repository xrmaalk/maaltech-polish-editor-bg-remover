# Changelog

## [1.1.2] – 2026-08-16

### Added
- Full Linux (x64) packaging path with PyInstaller one-file binary.
- Self-contained Linux install package (`MAALTECH-Polish-Editor-v1.1.2-linux-x64.tar.gz`) containing:
  - Portable binary
  - `install.sh` (user-local install into `~/.local`)
  - `uninstall.sh`
  - Desktop entry and icon
- Improved cross-platform icon handling (ICO on Windows, PNG via `iconphoto` on Linux).

### Changed
- Version bumped to 1.1.2 across source, Windows version resource, Inno Setup script, and desktop entry.
- Windows installer output filename now includes the version (`PolishEditorSetup-v1.1.2.exe`).
- `build_linux.sh` rewritten to use `PolishEditor-linux.spec`, run the rembg self-test, and produce a ready-to-install tarball.
- README rewritten for clear dual-platform (Windows + Linux/ChromeOS) documentation.

### Fixed
- Platform guards for DPI awareness and icon loading.
- Linux build no longer relies on incomplete ad-hoc PyInstaller flags; uses the dedicated spec file that correctly collects rembg / onnxruntime / pymatting.

## [1.1.1] – 2026-08-02

- Initial public Windows desktop release with face-aware polish, optional background removal, and Inno Setup installer.
