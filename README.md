# 🚀 QR Code Generator Pro

<p align="center">
  <img src="assets/icon.png" alt="QR Code Generator Icon" width="180" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-7C3AED.svg?style=for-the-badge" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge" alt="License MIT" />
  <img src="https://img.shields.io/badge/Security-SAST%20Audited-059669.svg?style=for-the-badge" alt="Security Audited" />
  <img src="https://img.shields.io/badge/i18n-TR%20%7C%20EN-blueviolet.svg?style=for-the-badge" alt="i18n Support" />
</p>

---

## 📚 Documentation Navigation / Dokümantasyon Rehberi

Explore the project documentation for setup, security guidelines, contribution rules, and release logs:

| Document | Content / İçerik | Link |
| :--- | :--- | :---: |
| 🐍 **Python Installation** | Direct download links (x64, ARM64, 32-bit) & setup instructions for Windows, macOS, Linux | [PYTHON_INSTALLATION.md](PYTHON_INSTALLATION.md) |
| 🛡️ **Security Policy** | Security vulnerability reporting, Bandit & pip-audit scanning standards | [SECURITY.md](SECURITY.md) |
| 🤝 **Contributing Guide** | Development setup, git workflow, and zero-comment code requirements | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 📜 **Code of Conduct** | Contributor Covenant v2.1 standards for open-source community | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |
| 📋 **Changelog** | Complete version history and release logs following Semantic Versioning | [CHANGELOG.md](CHANGELOG.md) |
| ⚖️ **License** | Terms and permissions under the MIT License | [LICENSE](LICENSE) |

---

## 📖 Overview / Genel Bakış

**QR Code Generator Pro** is a modern desktop application created by **Hasan Aras DEMİR** on August 2, 2026 (2 Ağustos 2026 Pazar). Built with Python 3.12 and `customtkinter`, it generates QR codes for URLs, plain text, vCards (contact cards), and Wi-Fi networks with live preview, branded design controls, logo embedding, and Turkish/English support.

---

## ✨ Features / Özellikler

- 🌐 **URL / Web Address**: Generate QR codes for websites with URL format validation.
- 📝 **Plain Text**: Encode notes, text, or custom content.
- 📇 **vCard 3.0**: Create contact card QR codes (First Name, Last Name, Phone, Email, Company, Title, Website, Address).
- 📶 **Wi-Fi Network**: Generate scan-to-connect Wi-Fi QR codes (WPA/WPA2/WPA3, WEP, WPA-Enterprise, WPS, and Open networks with hidden SSID support).
- 🎨 **Color Customization**: Customize QR code color, background color, box size, and border margins.
- 🪄 **Brand-ready Design**: Choose Classic, Ocean, Sunset, or Midnight presets; then refine module shapes, finder-eye styling, gradients, and logo frames.
- 🖼️ **Center Logo Embedding**: Add your logo or image to the center of the QR code (automatically sets High `H` error correction).
- 🩺 **Scan Health**: Clear built-in contrast, quiet-zone, and decoder-based verification feedback before you share a code.
- 💾 **Multi-Format Export**: Export high-resolution **PNG**, **JPEG**, **WebP**, or **SVG** files. Styled SVG exports preserve the preview appearance.
- 📋 **Faster Workflow**: Press `Ctrl+Enter` to generate, copy the encoded data in one click, and export controls remain disabled while content is out of date.
- 🌍 **Bilingual (i18n)**: Switch instantly between **Turkish (TR)** and **English (EN)**.
- 🌙 **Dark & Light Mode**: Modern interface matching system themes.
- ⚙️ **TOML Configuration**: Save settings automatically via `config.toml`.
- 🔒 **SAST & Security Audited**: Audited with `bandit`, `pip-audit`, and `ruff`.

---

## 📥 Quick Start & Setup / Kurulum

> 📌 **Installing Python for the first time?** Refer to **[PYTHON_INSTALLATION.md](PYTHON_INSTALLATION.md)** for direct `.exe` / `.pkg` download links and setup steps.

### Windows Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/HajxDeveloper-sys/QrGen-Windows.git
   cd QrGen-Windows
   ```

2. **Automated Setup & Launch**:
   Double-click:
   ```cmd
   install.bat
   ```
   *(Or execute `install.ps1` in PowerShell)*

3. **Manual Setup**:
   ```bash
   python -m venv venv
   venv\Scripts\python -m pip install -r requirements.txt
   venv\Scripts\python main.py
   ```

---

## 🚀 Usage / Kullanım

Launch the application using:

- **Windows Batch**: Double-click `run.bat` (or `run.ps1`)
- **Command Line**:
  ```bash
  venv\Scripts\python main.py
  ```

### Design and scan health

Use the **Design** panel to start from a visual preset or build a custom QR. The Scan Health card reports the lowest contrast, quiet-zone risks, and whether the generated image was independently decoded. A successful decoder check is the strongest signal; a “not independently verified” state means the decoder is unavailable, not that the code is necessarily unsafe. QR Generator saves your selected design defaults locally in `config.toml`.

---

## 🛡️ Security Audit / Siber Güvenlik Denetimi

Run static security and code quality scans locally:

```cmd
audit.bat
```
*(Or `audit.ps1` in PowerShell)*

For complete vulnerability reporting processes and security response protocols, see **[SECURITY.md](SECURITY.md)**.

---

## 🤝 Contributing / Katkıda Bulunma

We welcome contributions! Please review **[CONTRIBUTING.md](CONTRIBUTING.md)** before submitting pull requests. All contributions must adhere to our **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**.

---

## 📁 Project Structure / Proje Yapısı

```
QRCodeGenerator/
├── .github/
│   └── workflows/
│       └── security_audit.yml    # CI/CD Security Audit Workflow
├── assets/
│   ├── icon.ico                  # Taskbar & App Window Icon
│   └── icon.png                  # High-Res Application Icon
├── locale/
│   ├── en.json                   # English Dictionary
│   └── tr.json                   # Turkish Dictionary
├── src/
│   ├── __init__.py
│   ├── app.py                    # CustomTkinter GUI Application
│   ├── config_manager.py         # TOML Configuration Engine
│   ├── i18n.py                   # Internationalization Manager
│   ├── qr_engine.py              # Core QR Generator & Export Engine
│   ├── utils.py                  # Validation & Helper Utilities
│   ├── vcard_engine.py           # vCard 3.0 Format Builder
│   └── wifi_engine.py            # Wi-Fi String Formatter
├── tests/
│   ├── test_i18n.py
│   ├── test_qr_engine.py
│   └── test_wifi_engine.py
├── .gitattributes
├── .gitignore
├── CHANGELOG.md                  # Release Logs & History
├── CODE_OF_CONDUCT.md            # Community Guidelines
├── CONTRIBUTING.md               # Contribution Rules & Guidelines
├── LICENSE                       # MIT License
├── PYTHON_INSTALLATION.md        # Python Download & Setup Guide
├── README.md                     # Main Repository Overview
├── SECURITY.md                   # Security Audit & Policy
├── config.toml                   # User Configuration
├── install.bat / install.ps1     # Automated Installer Scripts
├── main.py                       # Application Entrypoint
├── requirements.txt              # Production Dependencies
├── requirements-dev.txt          # Developer Dependencies
└── run.bat / run.ps1             # Launch Scripts
```

---

## 📜 License & Copyright / Lisans ve Telif Hakkı

Copyright (c) 2026 **Hasan Aras DEMİR**. All rights reserved.

- 👤 **Project Creator & Rights Owner / Proje ve Hak Sahibi**: Hasan Aras DEMİR
- 📅 **Creation Date / Oluşturulma Tarihi**: 2 Ağustos 2026 Pazar (Sunday, August 2, 2026)

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
