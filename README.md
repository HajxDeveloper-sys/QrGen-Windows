# QR Code Generator

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Security Audit](https://github.com/yourusername/QRCodeGenerator/workflows/Security%20Audit/badge.svg)

Advanced QR Code Generator supporting URL, Text, vCard, and Wi-Fi.

## Features

- Generate QR codes for URLs, Text, vCards, and Wi-Fi networks
- Export in PNG, JPEG, and SVG formats
- Embed center logos automatically
- i18n support (English and Turkish)
- Dark and Light theme support
- Custom colors for QR codes
- TOML-based configuration

## Screenshots

*(Placeholder for screenshots)*

## Installation

For Python 3.12 installation instructions and direct downloads, see [PYTHON_INSTALLATION.md](PYTHON_INSTALLATION.md).

You can install dependencies via:
```bat
install.bat
```
Or manually:
```bat
pip install -r requirements.txt
```

## Usage

Start the application with:
```bat
run.bat
```
Or manually:
```bat
python main.py
```

## Security Audit

To run local security scans (Bandit, pip-audit, Ruff):
```bat
audit.bat
```

## Project Structure

```
QRCodeGenerator/
├── src/
├── assets/
├── locale/
├── .github/
├── main.py
├── requirements.txt
└── ...
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
