import json
from pathlib import Path

class I18nManager:
    def __init__(self, locale_dir: str = 'locale', default_language: str = 'tr'):
        self.locale_dir = Path(locale_dir)
        self.current_language = default_language
        self.translations: dict = {}
        self.load_language(default_language)

    def load_language(self, language_code: str) -> None:
        file_path = self.locale_dir / f'{language_code}.json'
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as file:
                self.translations = json.load(file)
        self.current_language = language_code

    def get(self, key: str) -> str:
        return self.translations.get(key, key)

    def get_available_languages(self) -> list[str]:
        if not self.locale_dir.exists():
            return []
        return [f.stem for f in self.locale_dir.glob('*.json')]
