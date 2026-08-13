from pathlib import Path

import tomli_w
import tomllib


class ConfigManager:
    def __init__(self, config_path: str = 'config.toml'):
        self.config_path = Path(config_path)
        self.config: dict = {}
        self.load()

    def load(self) -> None:
        if self.config_path.exists():
            with open(self.config_path, 'rb') as file:
                self.config = tomllib.load(file)
        else:
            self.config = self.get_default_config()
            self.save()

    def save(self) -> None:
        with open(self.config_path, 'wb') as file:
            tomli_w.dump(self.config, file)

    def get(self, section: str, key: str, default=None):
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value) -> None:
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()

    def update_section(self, section: str, values: dict) -> None:
        if section not in self.config:
            self.config[section] = {}
        self.config[section].update(values)
        self.save()

    def get_default_config(self) -> dict:
        return {
            "app": {
                "language": "tr",
                "theme": "dark",
                "default_export_format": "png"
            },
            "qr_defaults": {
                "box_size": 10,
                "border": 4,
                "error_correction": "M",
                "fill_color": "#000000",
                "back_color": "#FFFFFF",
                "module_style": "square",
                "eye_style": "square",
                "eye_fill_color": "",
                "eye_color_matches_qr": True,
                "gradient_type": "none",
                "gradient_color": "#2563EB",
                "logo_shape": "square"
            }
        }
