import json
from pathlib import Path

from src.i18n import I18nManager


class TestI18nManager:
    def test_load_english(self):
        manager = I18nManager(locale_dir="locale", default_language="en")
        assert manager.get("app_title") == "QR Code Generator"

    def test_load_turkish(self):
        manager = I18nManager(locale_dir="locale", default_language="tr")
        assert manager.get("app_title") == "QR Kod Üreteci"

    def test_missing_key_returns_key(self):
        manager = I18nManager(locale_dir="locale", default_language="en")
        assert manager.get("nonexistent_key") == "nonexistent_key"

    def test_available_languages(self):
        manager = I18nManager(locale_dir="locale", default_language="en")
        languages = manager.get_available_languages()
        assert "en" in languages
        assert "tr" in languages

    def test_language_switch(self):
        manager = I18nManager(locale_dir="locale", default_language="en")
        assert manager.get("app_title") == "QR Code Generator"
        manager.load_language("tr")
        assert manager.get("app_title") == "QR Kod Üreteci"

    def test_english_and_turkish_catalogs_have_the_same_keys(self):
        en_catalog = json.loads(Path("locale/en.json").read_text(encoding="utf-8"))
        tr_catalog = json.loads(Path("locale/tr.json").read_text(encoding="utf-8"))
        assert en_catalog.keys() == tr_catalog.keys()
