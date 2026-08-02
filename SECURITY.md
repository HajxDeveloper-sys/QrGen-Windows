# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report vulnerabilities by opening an issue or contacting the maintainers privately. We aim to acknowledge reports within 48 hours.

## Security Scanning

This project uses several tools for security auditing:
- **Bandit**: Finds common security issues in Python code.
- **pip-audit**: Scans Python environments for packages with known vulnerabilities.
- **Ruff**: Fast Python linter.

You can run the audit locally using the provided scripts:
- Windows (Batch): `audit.bat`
- Windows (PowerShell): `.\audit.ps1`
