# QR Studio for Windows

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

**QR Studio** is a privacy-first Windows desktop application built with Python 3.12 and `customtkinter`. It creates QR codes for URLs, text, contact cards and Wi-Fi networks without sending data to an external service.

---

## ✨ Features / Özellikler

- 🌐 **URL / Web Address**: Generate QR codes for websites with URL format validation.
- 📝 **Plain Text**: Encode notes, text, or custom content.
- 📇 **vCard 3.0**: Create contact card QR codes (First Name, Last Name, Phone, Email, Company, Title, Website, Address).
- 📶 **Wi-Fi Network**: Generate scan-to-connect Wi-Fi QR codes (WPA/WPA2/WPA3, WEP, WPA-Enterprise, WPS, and Open networks with hidden SSID support).
- 🎨 **Color Customization**: Customize QR code color, background color, box size, and border margins.
- 🖼️ **Center Logo Embedding**: Add your logo or image to the center of the QR code (automatically sets High `H` error correction).
- 💾 **Multi-Format Export**: Export in high-resolution **PNG**, **JPEG**, or vector **SVG**.
- 🌍 **Bilingual (i18n)**: Switch instantly between **Turkish (TR)** and **English (EN)**.
- 🌙 **Dark & Light Mode**: Modern interface matching system themes.
- ⚡ **Live Preview**: Debounced previews update as content or design settings change.
- 🧩 **Advanced Styling**: Square, rounded, circle, dot and gapped modules; custom corner and logo shapes; horizontal, vertical and radial gradients.
- ✅ **Readability Score**: Live contrast, quiet-zone and scan-safety diagnostics before export.
- 📦 **Extended Export**: PNG, JPEG, SVG and WebP from one focused export bar.
- 📋 **Fast Workflow**: Copy the encoded payload, clear the form and reset the design in one click; use `Ctrl+Enter` to generate and `Ctrl+S` to save PNG.
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
   pip install -r requirements.txt
   python main.py
   ```

---

## 🚀 Usage / Kullanım

Launch the application using:

- **Windows Batch**: Double-click `run.bat` (or `run.ps1`)
- **Command Line**:
  ```bash
  python main.py
  ```

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
