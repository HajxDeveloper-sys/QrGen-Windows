@echo off
pip install -r requirements-dev.txt
bandit -r src/ main.py
pip-audit
ruff check src/ main.py
exit
