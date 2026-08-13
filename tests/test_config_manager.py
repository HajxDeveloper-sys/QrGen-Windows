from src.config_manager import ConfigManager


def test_qr_design_defaults_are_created(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(str(config_path))

    assert manager.get("qr_defaults", "module_style") == "square"
    assert manager.get("qr_defaults", "eye_style") == "square"
    assert manager.get("qr_defaults", "gradient_type") == "none"
    assert manager.get("qr_defaults", "eye_color_matches_qr") is True


def test_qr_design_defaults_persist_in_one_update(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(str(config_path))
    manager.update_section(
        "qr_defaults",
        {
            "module_style": "rounded",
            "eye_style": "circle",
            "gradient_type": "radial",
            "gradient_color": "#2563EB",
            "logo_shape": "rounded",
        },
    )

    reloaded_manager = ConfigManager(str(config_path))
    assert reloaded_manager.get("qr_defaults", "module_style") == "rounded"
    assert reloaded_manager.get("qr_defaults", "eye_style") == "circle"
    assert reloaded_manager.get("qr_defaults", "gradient_type") == "radial"
    assert reloaded_manager.get("qr_defaults", "gradient_color") == "#2563EB"
    assert reloaded_manager.get("qr_defaults", "logo_shape") == "rounded"
