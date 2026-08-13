# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-13

### Added
- A dedicated design workspace with Classic, Ocean, Sunset, and Midnight presets.
- Module, finder-eye, gradient, and logo-frame controls that are applied consistently to preview and export.
- Scan Health feedback for contrast, quiet zone, design score, and decoder-based verification.
- WebP export, one-click payload copy, persistent design defaults, and `Ctrl+Enter` generation.
- Windows GitHub Actions application-test workflow.

### Changed
- Export and copy controls now stay disabled after content changes until the QR is regenerated.
- Styled SVG exports preserve the visual design using an embedded rendered image when vector primitives cannot represent it faithfully.
- Setup and launch scripts now use an isolated virtual environment and resolve their own folder.

## [1.0.0] - 2026-08-02 (2 Ağustos 2026 Pazar)

### Initial Release
- Project created and authored by **Hasan Aras DEMİR** on Sunday, August 2, 2026.

### Added
- URL, Text, vCard, and Wi-Fi QR code generation
- PNG, JPEG, and SVG export support
- Center logo embedding with auto High error correction
- Turkish and English language support (i18n)
- Dark and Light theme support
- Color customization for QR codes
- Security audit scripts (Bandit, pip-audit, Ruff)
- GitHub Actions CI/CD security workflow
