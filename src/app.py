import ctypes
from pathlib import Path
from tkinter import TclError, colorchooser, filedialog, messagebox
from typing import ClassVar

import customtkinter as ctk
from PIL import Image, ImageTk
from qrcode.exceptions import DataOverflowError

from src.config_manager import ConfigManager
from src.i18n import I18nManager
from src.qr_engine import QRCodeEngine, calculate_contrast_ratio, is_inverted
from src.utils import get_timestamp_string, validate_url
from src.vcard_engine import VCardEngine
from src.wifi_engine import WiFiQREngine


class QRCodeGeneratorApp(ctk.CTk):
    APPMODEL_ID = "QRCodeGenerator.App.1.0"
    MODULE_STYLES = ("square", "rounded", "circle", "dots", "gapped")
    EYE_STYLES = ("square", "rounded", "circle")
    GRADIENT_TYPES = ("none", "linear_h", "linear_v", "radial")
    LOGO_SHAPES = ("square", "rounded", "circle")
    PRESETS: ClassVar[dict[str, dict[str, str | bool]]] = {
        "classic": {
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
            "module_style": "square",
            "eye_style": "square",
            "eye_fill_color": "",
            "eye_color_matches_qr": True,
            "gradient_type": "none",
            "gradient_color": "#2563EB",
            "logo_shape": "square",
        },
        "ocean": {
            "fill_color": "#0F4C81",
            "back_color": "#F7FBFF",
            "module_style": "rounded",
            "eye_style": "rounded",
            "eye_fill_color": "#075985",
            "eye_color_matches_qr": False,
            "gradient_type": "linear_h",
            "gradient_color": "#0369A1",
            "logo_shape": "rounded",
        },
        "sunset": {
            "fill_color": "#7C2D12",
            "back_color": "#FFF7ED",
            "module_style": "dots",
            "eye_style": "circle",
            "eye_fill_color": "#9A3412",
            "eye_color_matches_qr": False,
            "gradient_type": "linear_v",
            "gradient_color": "#C2410C",
            "logo_shape": "circle",
        },
        "midnight": {
            "fill_color": "#111827",
            "back_color": "#F9FAFB",
            "module_style": "gapped",
            "eye_style": "rounded",
            "eye_fill_color": "#0F172A",
            "eye_color_matches_qr": False,
            "gradient_type": "radial",
            "gradient_color": "#1E3A8A",
            "logo_shape": "rounded",
        },
    }

    def __init__(self, base_path: Path = Path(".")):
        super().__init__()

        self.base_path = base_path
        self.config_manager = ConfigManager(str(base_path / "config.toml"))
        self.i18n = I18nManager(
            locale_dir=str(base_path / "locale"),
            default_language=self.config_manager.get("app", "language", "tr"),
        )
        self.qr_engine = QRCodeEngine()
        self.wifi_engine = WiFiQREngine()
        self.vcard_engine = VCardEngine()

        self.current_qr_image: Image.Image | None = None
        self.current_qr_data: str | None = None
        self.logo_path: str | None = None
        self._last_diagnostics: dict | None = None

        self.fill_color = self.config_manager.get("qr_defaults", "fill_color", "#000000")
        self.back_color = self.config_manager.get("qr_defaults", "back_color", "#FFFFFF")
        self.eye_fill_color = self.config_manager.get("qr_defaults", "eye_fill_color", "") or ""
        self.gradient_color = self.config_manager.get("qr_defaults", "gradient_color", "#2563EB")
        self._build_option_label_maps()
        self.module_style_key = self._configured_choice("module_style", self.MODULE_STYLES, "square")
        self.eye_style_key = self._configured_choice("eye_style", self.EYE_STYLES, "square")
        self.gradient_type_key = self._configured_choice("gradient_type", self.GRADIENT_TYPES, "none")
        self.logo_shape_key = self._configured_choice("logo_shape", self.LOGO_SHAPES, "square")
        self.eye_color_matches_qr = self.config_manager.get(
            "qr_defaults", "eye_color_matches_qr", not bool(self.eye_fill_color)
        )

        self._setup_taskbar_icon()
        self._setup_theme()
        self._setup_window()
        self._build_ui()
        self.bind_all("<Control-Return>", self._handle_generate_shortcut)

    def _configured_choice(self, key: str, allowed: tuple[str, ...], fallback: str) -> str:
        configured_value = self.config_manager.get("qr_defaults", key, fallback)
        return configured_value if configured_value in allowed else fallback

    def _build_option_label_maps(self) -> None:
        self._option_label_maps = {
            "module": {
                self.i18n.get(f"module_style_{value}"): value for value in self.MODULE_STYLES
            },
            "eye": {self.i18n.get(f"eye_style_{value}"): value for value in self.EYE_STYLES},
            "gradient": {
                self.i18n.get(f"gradient_{value}"): value for value in self.GRADIENT_TYPES
            },
            "logo": {
                self.i18n.get(f"logo_shape_{value}"): value for value in self.LOGO_SHAPES
            },
            "preset": {
                self.i18n.get(f"preset_{value}"): value for value in ("custom", *self.PRESETS)
            },
        }

    def _display_for_key(self, group: str, key: str) -> str:
        for display, value in self._option_label_maps[group].items():
            if value == key:
                return display
        return next(iter(self._option_label_maps[group]))

    def _key_for_display(self, group: str, display: str, fallback: str) -> str:
        return self._option_label_maps[group].get(display, fallback)

    def _setup_taskbar_icon(self) -> None:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APPMODEL_ID)
        except (AttributeError, OSError):
            return

    def _setup_theme(self) -> None:
        theme = self.config_manager.get("app", "theme", "dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

    def _setup_window(self) -> None:
        self.title(self.i18n.get("app_title"))
        self.geometry("1180x820")
        self.minsize(1050, 760)
        self._apply_window_icon()

    def _apply_window_icon(self) -> None:
        icon_ico_path = self.base_path / "assets" / "icon.ico"
        icon_png_path = self.base_path / "assets" / "icon.png"

        if icon_ico_path.exists():
            self.iconbitmap(str(icon_ico_path))

        if icon_png_path.exists():
            try:
                icon_image = ImageTk.PhotoImage(Image.open(icon_png_path))
                self.wm_iconphoto(True, icon_image)
                self._taskbar_icon_ref = icon_image
            except (OSError, TclError):
                return

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self) -> None:
        self.left_frame = ctk.CTkFrame(self, corner_radius=15)
        self.left_frame.grid(row=0, column=0, padx=(15, 7), pady=15, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        self._build_settings_bar()
        self._build_tabview()
        self._build_customization_panel()
        self._build_action_buttons()

    def _build_settings_bar(self) -> None:
        self.settings_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.settings_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.language_label = ctk.CTkLabel(self.settings_frame, text=self.i18n.get("label_language"))
        self.language_label.grid(row=0, column=0, padx=(5, 5))
        self.language_var = ctk.StringVar(
            value=self.config_manager.get("app", "language", "tr").upper()
        )
        self.language_selector = ctk.CTkSegmentedButton(
            self.settings_frame,
            values=["TR", "EN"],
            variable=self.language_var,
            command=self._on_language_change,
        )
        self.language_selector.grid(row=0, column=1, padx=5)

        self.theme_label = ctk.CTkLabel(self.settings_frame, text=self.i18n.get("label_theme"))
        self.theme_label.grid(row=0, column=2, padx=(20, 5))
        self.theme_var = ctk.StringVar(value=self.config_manager.get("app", "theme", "dark"))
        self.theme_selector = ctk.CTkSegmentedButton(
            self.settings_frame,
            values=["dark", "light"],
            variable=self.theme_var,
            command=self._on_theme_change,
        )
        self.theme_selector.grid(row=0, column=3, padx=5)

    def _build_tabview(self) -> None:
        self.tabview = ctk.CTkTabview(self.left_frame, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.tab_url = self.tabview.add(self.i18n.get("tab_url"))
        self.tab_text = self.tabview.add(self.i18n.get("tab_text"))
        self.tab_vcard = self.tabview.add(self.i18n.get("tab_vcard"))
        self.tab_wifi = self.tabview.add(self.i18n.get("tab_wifi"))
        self._stored_tab_names = {
            "url": self.i18n.get("tab_url"),
            "text": self.i18n.get("tab_text"),
            "vcard": self.i18n.get("tab_vcard"),
            "wifi": self.i18n.get("tab_wifi"),
        }
        self._build_url_tab()
        self._build_text_tab()
        self._build_vcard_tab()
        self._build_wifi_tab()
        self._bind_input_events()

    def _build_url_tab(self) -> None:
        self.tab_url.grid_columnconfigure(0, weight=1)
        self.url_label = ctk.CTkLabel(
            self.tab_url,
            text=self.i18n.get("label_url"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.url_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")
        self.url_entry = ctk.CTkEntry(
            self.tab_url,
            placeholder_text="https://example.com",
            height=40,
        )
        self.url_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

    def _build_text_tab(self) -> None:
        self.tab_text.grid_columnconfigure(0, weight=1)
        self.tab_text.grid_rowconfigure(1, weight=1)
        self.text_label = ctk.CTkLabel(
            self.tab_text,
            text=self.i18n.get("label_text"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.text_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")
        self.text_input = ctk.CTkTextbox(self.tab_text, height=120)
        self.text_input.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

    def _build_vcard_tab(self) -> None:
        self.tab_vcard.grid_columnconfigure(1, weight=1)
        self.vcard_field_definitions = [
            ("label_first_name", "first_name"),
            ("label_last_name", "last_name"),
            ("label_phone", "phone"),
            ("label_email", "email"),
            ("label_company", "company"),
            ("label_title", "title"),
            ("label_website", "website"),
            ("label_address", "address"),
        ]
        self.vcard_labels: dict[str, ctk.CTkLabel] = {}
        self.vcard_entries: dict[str, ctk.CTkEntry] = {}
        for row_index, (label_key, field_name) in enumerate(self.vcard_field_definitions):
            label = ctk.CTkLabel(self.tab_vcard, text=self.i18n.get(label_key))
            label.grid(row=row_index, column=0, padx=(10, 5), pady=3, sticky="w")
            self.vcard_labels[field_name] = label
            entry = ctk.CTkEntry(self.tab_vcard, height=32)
            entry.grid(row=row_index, column=1, padx=(5, 10), pady=3, sticky="ew")
            self.vcard_entries[field_name] = entry

    def _build_wifi_tab(self) -> None:
        self.tab_wifi.grid_columnconfigure(1, weight=1)
        self.wifi_ssid_label = ctk.CTkLabel(self.tab_wifi, text=self.i18n.get("label_ssid"))
        self.wifi_ssid_label.grid(row=0, column=0, padx=(10, 5), pady=(15, 5), sticky="w")
        self.wifi_ssid_entry = ctk.CTkEntry(self.tab_wifi, height=35)
        self.wifi_ssid_entry.grid(row=0, column=1, padx=(5, 10), pady=(15, 5), sticky="ew")
        self.wifi_password_label = ctk.CTkLabel(self.tab_wifi, text=self.i18n.get("label_password"))
        self.wifi_password_label.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        self.wifi_password_entry = ctk.CTkEntry(self.tab_wifi, height=35, show="*")
        self.wifi_password_entry.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="ew")
        self.wifi_encryption_label = ctk.CTkLabel(
            self.tab_wifi, text=self.i18n.get("label_encryption")
        )
        self.wifi_encryption_label.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="w")
        self.wifi_encryption_var = ctk.StringVar(value="WPA")
        self.wifi_encryption_menu = ctk.CTkOptionMenu(
            self.tab_wifi,
            values=["WPA", "WPA2", "WPA3", "WEP", "WPA-Enterprise", "WPS", "nopass"],
            variable=self.wifi_encryption_var,
            height=35,
        )
        self.wifi_encryption_menu.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="ew")
        self.wifi_hidden_label = ctk.CTkLabel(self.tab_wifi, text=self.i18n.get("label_hidden"))
        self.wifi_hidden_label.grid(row=3, column=0, padx=(10, 5), pady=5, sticky="w")
        self.wifi_hidden_var = ctk.BooleanVar(value=False)
        self.wifi_hidden_switch = ctk.CTkSwitch(
            self.tab_wifi,
            text="",
            variable=self.wifi_hidden_var,
        )
        self.wifi_hidden_switch.grid(row=3, column=1, padx=(5, 10), pady=5, sticky="w")

    def _bind_input_events(self) -> None:
        for widget in [self.url_entry, self.text_input, self.wifi_ssid_entry, self.wifi_password_entry]:
            widget.bind("<KeyRelease>", self._mark_qr_stale, add="+")
        for entry in self.vcard_entries.values():
            entry.bind("<KeyRelease>", self._mark_qr_stale, add="+")
        self.wifi_encryption_menu.configure(command=self._mark_qr_stale)
        self.wifi_hidden_switch.configure(command=self._mark_qr_stale)

    def _build_customization_panel(self) -> None:
        self.custom_frame = ctk.CTkFrame(self.left_frame, corner_radius=10)
        self.custom_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.custom_frame.grid_columnconfigure(1, weight=1)
        self.design_header_label = ctk.CTkLabel(
            self.custom_frame,
            text=self.i18n.get("label_design"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.design_header_label.grid(row=0, column=0, padx=(10, 5), pady=(8, 2), sticky="w")
        self.preset_label = ctk.CTkLabel(self.custom_frame, text=self.i18n.get("label_preset"))
        self.preset_label.grid(row=0, column=1, padx=(5, 5), pady=(8, 2), sticky="e")
        self.preset_var = ctk.StringVar(value=self._display_for_key("preset", "custom"))
        self.preset_menu = ctk.CTkOptionMenu(
            self.custom_frame,
            values=list(self._option_label_maps["preset"]),
            variable=self.preset_var,
            command=self._apply_preset,
            width=155,
            height=30,
        )
        self.preset_menu.grid(row=0, column=2, padx=(0, 10), pady=(8, 2), sticky="e")

        self.design_tabview = ctk.CTkTabview(self.custom_frame, corner_radius=8, height=242)
        self.design_tabview.grid(row=1, column=0, columnspan=3, padx=8, pady=(2, 8), sticky="ew")
        self._stored_design_tab_names = {
            "basics": self.i18n.get("tab_basics"),
            "style": self.i18n.get("tab_style"),
        }
        self.basics_tab = self.design_tabview.add(self._stored_design_tab_names["basics"])
        self.style_tab = self.design_tabview.add(self._stored_design_tab_names["style"])
        self._build_basics_tab()
        self._build_style_tab()

    def _build_basics_tab(self) -> None:
        self.basics_tab.grid_columnconfigure((0, 1, 2), weight=1)
        self.fill_color_button = ctk.CTkButton(
            self.basics_tab,
            text=self.i18n.get("label_fill_color"),
            command=self._pick_fill_color,
            height=34,
        )
        self.fill_color_button.grid(row=0, column=0, padx=5, pady=(8, 4), sticky="ew")
        self.back_color_button = ctk.CTkButton(
            self.basics_tab,
            text=self.i18n.get("label_back_color"),
            command=self._pick_back_color,
            height=34,
        )
        self.back_color_button.grid(row=0, column=1, padx=5, pady=(8, 4), sticky="ew")
        self.logo_button = ctk.CTkButton(
            self.basics_tab,
            text=self.i18n.get("btn_select_logo"),
            command=self._select_logo,
            height=34,
        )
        self.logo_button.grid(row=0, column=2, padx=5, pady=(8, 4), sticky="ew")

        self.box_size_label = ctk.CTkLabel(self.basics_tab, text=self.i18n.get("label_box_size"))
        self.box_size_label.grid(row=1, column=0, padx=5, pady=(3, 0), sticky="w")
        self.border_label = ctk.CTkLabel(self.basics_tab, text=self.i18n.get("label_border"))
        self.border_label.grid(row=1, column=1, padx=5, pady=(3, 0), sticky="w")
        self.error_correction_label = ctk.CTkLabel(
            self.basics_tab, text=self.i18n.get("label_error_correction")
        )
        self.error_correction_label.grid(row=1, column=2, padx=5, pady=(3, 0), sticky="w")

        self.box_size_var = ctk.IntVar(
            value=self.config_manager.get("qr_defaults", "box_size", 10)
        )
        self.box_size_slider = ctk.CTkSlider(
            self.basics_tab,
            from_=5,
            to=20,
            number_of_steps=15,
            variable=self.box_size_var,
            command=self._on_design_changed,
        )
        self.box_size_slider.grid(row=2, column=0, padx=5, pady=(0, 3), sticky="ew")
        self.box_size_value_label = ctk.CTkLabel(self.basics_tab, textvariable=self.box_size_var)
        self.box_size_value_label.grid(row=2, column=0, padx=5, pady=(0, 3), sticky="e")

        self.border_var = ctk.IntVar(value=self.config_manager.get("qr_defaults", "border", 4))
        self.border_slider = ctk.CTkSlider(
            self.basics_tab,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.border_var,
            command=self._on_design_changed,
        )
        self.border_slider.grid(row=2, column=1, padx=5, pady=(0, 3), sticky="ew")
        self.border_value_label = ctk.CTkLabel(self.basics_tab, textvariable=self.border_var)
        self.border_value_label.grid(row=2, column=1, padx=5, pady=(0, 3), sticky="e")

        self.error_correction_var = ctk.StringVar(
            value=self.config_manager.get("qr_defaults", "error_correction", "M")
        )
        self.error_correction_menu = ctk.CTkOptionMenu(
            self.basics_tab,
            values=["L", "M", "Q", "H"],
            variable=self.error_correction_var,
            command=self._on_design_changed,
            height=30,
        )
        self.error_correction_menu.grid(row=2, column=2, padx=5, pady=(0, 3), sticky="ew")

        self.logo_status_label = ctk.CTkLabel(self.basics_tab, text="", font=ctk.CTkFont(size=11))
        self.logo_status_label.grid(row=3, column=0, columnspan=2, padx=5, pady=(3, 0), sticky="w")
        self.remove_logo_button = ctk.CTkButton(
            self.basics_tab,
            text=self.i18n.get("btn_remove_logo"),
            command=self._remove_logo,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            height=30,
            state="disabled",
        )
        self.remove_logo_button.grid(row=3, column=2, padx=5, pady=(3, 0), sticky="ew")

        self.contrast_warning_label = ctk.CTkLabel(
            self.basics_tab,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#EF4444",
            wraplength=500,
        )
        self.contrast_warning_label.grid(row=4, column=0, columnspan=3, padx=5, pady=(3, 0), sticky="w")
        self.fix_contrast_button = ctk.CTkButton(
            self.basics_tab,
            text=self.i18n.get("btn_fix_contrast"),
            command=self._fix_color_contrast,
            height=30,
            fg_color="#D97706",
            hover_color="#B45309",
        )
        self.fix_contrast_button.grid(row=5, column=0, columnspan=3, padx=5, pady=(3, 2), sticky="ew")
        self.save_defaults_button = ctk.CTkButton(
            self.basics_tab,
            text=self.i18n.get("btn_save_defaults"),
            command=self._save_current_defaults,
            height=30,
            fg_color="#475569",
            hover_color="#334155",
        )
        self.save_defaults_button.grid(row=6, column=0, columnspan=3, padx=5, pady=(2, 6), sticky="ew")
        self._update_color_buttons()
        self._check_contrast()

    def _build_style_tab(self) -> None:
        self.style_tab.grid_columnconfigure((0, 1), weight=1)
        self.module_style_label = ctk.CTkLabel(
            self.style_tab, text=self.i18n.get("label_module_style")
        )
        self.module_style_label.grid(row=0, column=0, padx=5, pady=(8, 0), sticky="w")
        self.eye_style_label = ctk.CTkLabel(self.style_tab, text=self.i18n.get("label_eye_style"))
        self.eye_style_label.grid(row=0, column=1, padx=5, pady=(8, 0), sticky="w")
        self.module_style_var = ctk.StringVar(
            value=self._display_for_key("module", self.module_style_key)
        )
        self.module_style_menu = ctk.CTkOptionMenu(
            self.style_tab,
            values=list(self._option_label_maps["module"]),
            variable=self.module_style_var,
            command=self._on_design_changed,
            height=30,
        )
        self.module_style_menu.grid(row=1, column=0, padx=5, pady=(0, 4), sticky="ew")
        self.eye_style_var = ctk.StringVar(value=self._display_for_key("eye", self.eye_style_key))
        self.eye_style_menu = ctk.CTkOptionMenu(
            self.style_tab,
            values=list(self._option_label_maps["eye"]),
            variable=self.eye_style_var,
            command=self._on_design_changed,
            height=30,
        )
        self.eye_style_menu.grid(row=1, column=1, padx=5, pady=(0, 4), sticky="ew")

        self.eye_color_matches_var = ctk.BooleanVar(value=bool(self.eye_color_matches_qr))
        self.eye_color_button = ctk.CTkButton(
            self.style_tab,
            text=self.i18n.get("label_eye_color"),
            command=self._pick_eye_color,
            height=32,
        )
        self.eye_color_button.grid(row=2, column=0, padx=5, pady=(3, 4), sticky="ew")
        self.eye_color_matches_switch = ctk.CTkSwitch(
            self.style_tab,
            text=self.i18n.get("label_match_qr_color"),
            variable=self.eye_color_matches_var,
            command=self._on_eye_color_match_changed,
        )
        self.eye_color_matches_switch.grid(row=2, column=1, padx=5, pady=(3, 4), sticky="w")

        self.gradient_label = ctk.CTkLabel(self.style_tab, text=self.i18n.get("label_gradient"))
        self.gradient_label.grid(row=3, column=0, padx=5, pady=(3, 0), sticky="w")
        self.logo_shape_label = ctk.CTkLabel(self.style_tab, text=self.i18n.get("label_logo_shape"))
        self.logo_shape_label.grid(row=3, column=1, padx=5, pady=(3, 0), sticky="w")
        self.gradient_type_var = ctk.StringVar(
            value=self._display_for_key("gradient", self.gradient_type_key)
        )
        self.gradient_type_menu = ctk.CTkOptionMenu(
            self.style_tab,
            values=list(self._option_label_maps["gradient"]),
            variable=self.gradient_type_var,
            command=self._on_gradient_changed,
            height=30,
        )
        self.gradient_type_menu.grid(row=4, column=0, padx=5, pady=(0, 4), sticky="ew")
        self.logo_shape_var = ctk.StringVar(value=self._display_for_key("logo", self.logo_shape_key))
        self.logo_shape_menu = ctk.CTkOptionMenu(
            self.style_tab,
            values=list(self._option_label_maps["logo"]),
            variable=self.logo_shape_var,
            command=self._on_design_changed,
            height=30,
        )
        self.logo_shape_menu.grid(row=4, column=1, padx=5, pady=(0, 4), sticky="ew")

        self.gradient_color_button = ctk.CTkButton(
            self.style_tab,
            text=self.i18n.get("label_gradient_color"),
            command=self._pick_gradient_color,
            height=32,
        )
        self.gradient_color_button.grid(row=5, column=0, columnspan=2, padx=5, pady=(3, 8), sticky="ew")
        self._update_style_control_states()

    def _build_action_buttons(self) -> None:
        self.action_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.action_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.generate_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_generate"),
            command=self._generate_qr,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
        )
        self.generate_button.grid(row=0, column=0, columnspan=4, padx=5, pady=(2, 5), sticky="ew")
        self.save_png_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_save_png"),
            command=lambda: self._save_qr("png"),
            height=34,
            fg_color="#059669",
            hover_color="#047857",
            state="disabled",
        )
        self.save_png_button.grid(row=1, column=0, padx=3, pady=2, sticky="ew")
        self.save_jpeg_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_save_jpeg"),
            command=lambda: self._save_qr("jpeg"),
            height=34,
            fg_color="#D97706",
            hover_color="#B45309",
            state="disabled",
        )
        self.save_jpeg_button.grid(row=1, column=1, padx=3, pady=2, sticky="ew")
        self.save_svg_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_save_svg"),
            command=lambda: self._save_qr("svg"),
            height=34,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            state="disabled",
        )
        self.save_svg_button.grid(row=1, column=2, padx=3, pady=2, sticky="ew")
        self.save_webp_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_save_webp"),
            command=lambda: self._save_qr("webp"),
            height=34,
            fg_color="#0F766E",
            hover_color="#115E59",
            state="disabled",
        )
        self.save_webp_button.grid(row=1, column=3, padx=3, pady=2, sticky="ew")
        self.copy_data_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_copy_data"),
            command=self._copy_qr_data,
            height=32,
            state="disabled",
        )
        self.copy_data_button.grid(row=2, column=0, columnspan=4, padx=5, pady=(3, 1), sticky="ew")
        self.copy_status_label = ctk.CTkLabel(
            self.action_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#059669",
        )
        self.copy_status_label.grid(row=3, column=0, columnspan=4, padx=5, pady=(0, 1), sticky="w")
        self.shortcut_label = ctk.CTkLabel(
            self.action_frame,
            text=self.i18n.get("shortcut_generate"),
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray65"),
        )
        self.shortcut_label.grid(row=4, column=0, columnspan=4, padx=5, pady=(0, 1), sticky="e")
        self.output_action_buttons = [
            self.save_png_button,
            self.save_jpeg_button,
            self.save_svg_button,
            self.save_webp_button,
            self.copy_data_button,
        ]

    def _build_right_panel(self) -> None:
        self.right_frame = ctk.CTkFrame(self, corner_radius=15)
        self.right_frame.grid(row=0, column=1, padx=(7, 15), pady=15, sticky="nsew")
        self.right_frame.grid_rowconfigure(2, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.preview_title_label = ctk.CTkLabel(
            self.right_frame,
            text=self.i18n.get("label_preview"),
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.preview_title_label.grid(row=0, column=0, padx=15, pady=(15, 5))
        self.health_frame = ctk.CTkFrame(self.right_frame, corner_radius=10, fg_color=("gray92", "gray17"))
        self.health_frame.grid(row=1, column=0, padx=15, pady=(3, 5), sticky="ew")
        self.health_frame.grid_columnconfigure(0, weight=1)
        self.health_title_label = ctk.CTkLabel(
            self.health_frame,
            text=self.i18n.get("label_scannability"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.health_title_label.grid(row=0, column=0, padx=10, pady=(7, 0), sticky="w")
        self.health_status_label = ctk.CTkLabel(
            self.health_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=340,
            justify="left",
        )
        self.health_status_label.grid(row=1, column=0, padx=10, pady=(1, 0), sticky="w")
        self.health_detail_label = ctk.CTkLabel(
            self.health_frame,
            text="",
            font=ctk.CTkFont(size=11),
            wraplength=340,
            justify="left",
        )
        self.health_detail_label.grid(row=2, column=0, padx=10, pady=(1, 7), sticky="w")
        self.preview_canvas_frame = ctk.CTkFrame(
            self.right_frame,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
        )
        self.preview_canvas_frame.grid(row=2, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.preview_canvas_frame.grid_rowconfigure(0, weight=1)
        self.preview_canvas_frame.grid_columnconfigure(0, weight=1)
        self.preview_canvas_frame.bind("<Configure>", self._on_preview_frame_resize)
        self.preview_image_label = ctk.CTkLabel(self.preview_canvas_frame, text="")
        self.preview_image_label.grid(row=0, column=0, padx=10, pady=10)
        self._set_health_idle()
        self._show_placeholder_preview()

    def _on_preview_frame_resize(self, _event=None) -> None:
        if hasattr(self, "_current_raw_pil_image") and self._current_raw_pil_image:
            self._render_scaled_preview(self._current_raw_pil_image)

    def _show_placeholder_preview(self) -> None:
        placeholder = Image.new("RGBA", (300, 300), (200, 200, 200, 50))
        self._display_preview_image(placeholder)

    def _display_preview_image(self, pil_image: Image.Image) -> None:
        self._current_raw_pil_image = pil_image
        self._render_scaled_preview(pil_image)

    def _render_scaled_preview(self, pil_image: Image.Image) -> None:
        self.update_idletasks()
        frame_width = self.preview_canvas_frame.winfo_width()
        frame_height = self.preview_canvas_frame.winfo_height()
        max_width = max(180, frame_width - 30) if frame_width > 1 else 320
        max_height = max(180, frame_height - 30) if frame_height > 1 else 320
        target_size = min(max_width, max_height)
        image_copy = pil_image.copy()
        image_copy.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        self.preview_ctk_image = ctk.CTkImage(
            light_image=image_copy,
            dark_image=image_copy,
            size=image_copy.size,
        )
        self.preview_image_label.configure(image=self.preview_ctk_image, text="")

    def _set_output_actions_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for button in self.output_action_buttons:
            button.configure(state=state)

    def _set_health_idle(self, stale: bool = False) -> None:
        if stale:
            self.health_status_label.configure(
                text=self.i18n.get("msg_qr_outdated"), text_color="#D97706"
            )
        else:
            self.health_status_label.configure(text="", text_color=("gray35", "gray70"))
        self.health_detail_label.configure(text="")

    def _check_contrast(self) -> None:
        ratio = calculate_contrast_ratio(self.fill_color, self.back_color)
        inverted = is_inverted(self.fill_color, self.back_color)
        if inverted:
            self.contrast_warning_label.configure(
                text=self.i18n.get("warn_inverted"), text_color="#EF4444"
            )
            self.fix_contrast_button.grid()
        elif ratio < 4.0:
            self.contrast_warning_label.configure(
                text=f"{self.i18n.get('warn_low_contrast')} (1:{ratio:.1f})",
                text_color="#F59E0B",
            )
            self.fix_contrast_button.grid()
        else:
            self.contrast_warning_label.configure(text="")
            self.fix_contrast_button.grid_remove()

    def _fix_color_contrast(self) -> None:
        if is_inverted(self.fill_color, self.back_color):
            self.fill_color, self.back_color = self.back_color, self.fill_color
        else:
            self.fill_color, self.back_color = "#000000", "#FFFFFF"
        self._set_preset_key("custom")
        self._update_color_buttons()
        self._check_contrast()
        self._regenerate_current_qr()

    def _configure_color_button(self, button: ctk.CTkButton, color: str, text: str) -> None:
        display_color = color if color.upper() != "#FFFFFF" else "#E0E0E0"
        hover_color = self._adjust_brightness(display_color, -25)
        text_color = "#000000" if self._is_light_color(display_color) else "#FFFFFF"
        button.configure(
            text=text,
            fg_color=display_color,
            hover_color=hover_color,
            text_color=text_color,
        )

    def _update_color_buttons(self) -> None:
        self._configure_color_button(
            self.fill_color_button, self.fill_color, self.i18n.get("label_fill_color")
        )
        self._configure_color_button(
            self.back_color_button, self.back_color, self.i18n.get("label_back_color")
        )
        if hasattr(self, "eye_color_button"):
            effective_eye_color = self.fill_color if self.eye_color_matches_var.get() else self.eye_fill_color
            self._configure_color_button(
                self.eye_color_button, effective_eye_color, self.i18n.get("label_eye_color")
            )
            self._update_style_control_states()

    def _update_style_control_states(self) -> None:
        eye_state = "disabled" if self.eye_color_matches_var.get() else "normal"
        self.eye_color_button.configure(state=eye_state)
        gradient_key = self._key_for_display(
            "gradient", self.gradient_type_var.get(), "none"
        )
        gradient_state = "normal" if gradient_key != "none" else "disabled"
        self.gradient_color_button.configure(state=gradient_state)
        self._configure_color_button(
            self.gradient_color_button,
            self.gradient_color,
            self.i18n.get("label_gradient_color"),
        )
        self.gradient_color_button.configure(state=gradient_state)

    def _pick_fill_color(self) -> None:
        color = colorchooser.askcolor(
            initialcolor=self.fill_color,
            title=self.i18n.get("label_fill_color"),
        )
        if color and color[1]:
            self.fill_color = color[1]
            self._set_preset_key("custom")
            self._update_color_buttons()
            self._check_contrast()
            self._regenerate_current_qr()

    def _pick_back_color(self) -> None:
        color = colorchooser.askcolor(
            initialcolor=self.back_color,
            title=self.i18n.get("label_back_color"),
        )
        if color and color[1]:
            self.back_color = color[1]
            self._set_preset_key("custom")
            self._update_color_buttons()
            self._check_contrast()
            self._regenerate_current_qr()

    def _pick_eye_color(self) -> None:
        color = colorchooser.askcolor(
            initialcolor=self.eye_fill_color or self.fill_color,
            title=self.i18n.get("label_eye_color"),
        )
        if color and color[1]:
            self.eye_fill_color = color[1]
            self.eye_color_matches_var.set(False)
            self._set_preset_key("custom")
            self._update_color_buttons()
            self._regenerate_current_qr()

    def _pick_gradient_color(self) -> None:
        color = colorchooser.askcolor(
            initialcolor=self.gradient_color,
            title=self.i18n.get("label_gradient_color"),
        )
        if color and color[1]:
            self.gradient_color = color[1]
            self._set_preset_key("custom")
            self._update_style_control_states()
            self._regenerate_current_qr()

    def _on_eye_color_match_changed(self) -> None:
        if not self.eye_color_matches_var.get() and not self.eye_fill_color:
            self.eye_fill_color = self.fill_color
        self._set_preset_key("custom")
        self._update_color_buttons()
        self._regenerate_current_qr()

    def _on_gradient_changed(self, _selection: str) -> None:
        self._set_preset_key("custom")
        self._update_style_control_states()
        self._regenerate_current_qr()

    def _on_design_changed(self, *_args) -> None:
        self._set_preset_key("custom")
        self._regenerate_current_qr()

    def _apply_preset(self, selection: str) -> None:
        preset_key = self._key_for_display("preset", selection, "custom")
        if preset_key == "custom":
            return
        preset = self.PRESETS[preset_key]
        self.fill_color = preset["fill_color"]
        self.back_color = preset["back_color"]
        self.eye_fill_color = preset["eye_fill_color"]
        self.eye_color_matches_var.set(preset["eye_color_matches_qr"])
        self.module_style_var.set(self._display_for_key("module", preset["module_style"]))
        self.eye_style_var.set(self._display_for_key("eye", preset["eye_style"]))
        self.gradient_type_var.set(self._display_for_key("gradient", preset["gradient_type"]))
        self.logo_shape_var.set(self._display_for_key("logo", preset["logo_shape"]))
        self.gradient_color = preset["gradient_color"]
        self._update_color_buttons()
        self._check_contrast()
        self._regenerate_current_qr()

    def _set_preset_key(self, preset_key: str) -> None:
        if hasattr(self, "preset_var"):
            self.preset_var.set(self._display_for_key("preset", preset_key))

    def _select_logo(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.ico")]
        )
        if file_path:
            self.logo_path = file_path
            self.logo_status_label.configure(text=Path(file_path).name)
            self.remove_logo_button.configure(state="normal")
            self._regenerate_current_qr()

    def _remove_logo(self) -> None:
        self.logo_path = None
        self.logo_status_label.configure(text="")
        self.remove_logo_button.configure(state="disabled")
        self._regenerate_current_qr()

    def _get_active_tab_name(self) -> str:
        current_tab = self.tabview.get()
        tab_mapping = {name: key for key, name in self._stored_tab_names.items()}
        return tab_mapping.get(current_tab, "url")

    def _collect_qr_data(self) -> str | None:
        active_tab = self._get_active_tab_name()
        if active_tab == "url":
            qr_data = self.url_entry.get().strip()
            if not qr_data:
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
                return None
            if not validate_url(qr_data):
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_invalid_url"))
                return None
            return qr_data
        if active_tab == "text":
            qr_data = self.text_input.get("1.0", "end-1c").strip()
            if not qr_data:
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
                return None
            return qr_data
        if active_tab == "vcard":
            first_name = self.vcard_entries["first_name"].get().strip()
            last_name = self.vcard_entries["last_name"].get().strip()
            if not first_name and not last_name:
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
                return None
            return self.vcard_engine.generate_vcard_string(
                first_name=first_name,
                last_name=last_name,
                phone=self.vcard_entries["phone"].get().strip(),
                email=self.vcard_entries["email"].get().strip(),
                company=self.vcard_entries["company"].get().strip(),
                title=self.vcard_entries["title"].get().strip(),
                website=self.vcard_entries["website"].get().strip(),
                address=self.vcard_entries["address"].get().strip(),
            )
        ssid = self.wifi_ssid_entry.get().strip()
        if not ssid:
            messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
            return None
        return self.wifi_engine.generate_wifi_string(
            ssid,
            self.wifi_password_entry.get().strip(),
            self.wifi_encryption_var.get(),
            self.wifi_hidden_var.get(),
        )

    def _current_design_options(self) -> dict:
        gradient_type = self._key_for_display(
            "gradient", self.gradient_type_var.get(), "none"
        )
        return {
            "module_style": self._key_for_display(
                "module", self.module_style_var.get(), "square"
            ),
            "eye_style": self._key_for_display("eye", self.eye_style_var.get(), "square"),
            "eye_fill_color": (
                None if self.eye_color_matches_var.get() else self.eye_fill_color
            ),
            "gradient_type": None if gradient_type == "none" else gradient_type,
            "gradient_color": self.gradient_color if gradient_type != "none" else None,
            "logo_shape": self._key_for_display("logo", self.logo_shape_var.get(), "square"),
        }

    def _create_qr_image(self, qr_data: str) -> Image.Image:
        return self.qr_engine.generate_qr(
            data=qr_data,
            fill_color=self.fill_color,
            back_color=self.back_color,
            box_size=self.box_size_var.get(),
            border=self.border_var.get(),
            error_correction=self.error_correction_var.get(),
            logo_path=self.logo_path,
            **self._current_design_options(),
        )

    def _generate_qr(self) -> None:
        qr_data = self._collect_qr_data()
        if qr_data is None:
            return
        self.current_qr_data = qr_data
        self._render_current_qr()

    def _regenerate_current_qr(self) -> None:
        if self.current_qr_data:
            self._render_current_qr()

    def _render_current_qr(self) -> None:
        if not self.current_qr_data:
            return
        try:
            self.current_qr_image = self._create_qr_image(self.current_qr_data)
            self._display_preview_image(self.current_qr_image)
            self._set_output_actions_enabled(True)
            self.copy_status_label.configure(text="")
            self._update_health_feedback(self.current_qr_data)
            self._persist_qr_defaults()
        except (DataOverflowError, OSError, RuntimeError, ValueError) as generation_error:
            self._set_output_actions_enabled(False)
            messagebox.showerror(self.i18n.get("msg_error"), str(generation_error))

    def _update_health_feedback(self, qr_data: str) -> None:
        design = self._current_design_options()
        diagnostics = self.qr_engine.analyze_scannability(
            data=qr_data,
            fill_color=self.fill_color,
            back_color=self.back_color,
            box_size=self.box_size_var.get(),
            border=self.border_var.get(),
            error_correction=self.error_correction_var.get(),
            logo_path=self.logo_path,
            **design,
        )
        self._last_diagnostics = diagnostics
        scan_info = diagnostics.get("scan_verification", {})
        decoder_available = scan_info.get("engine") == "zxingcpp"
        verified = (
            decoder_available
            and scan_info.get("scannable") is True
            and scan_info.get("decoded_text") == qr_data
        )
        if verified:
            status = self.i18n.get("health_verified")
            status_color = "#059669"
        elif decoder_available:
            status = self.i18n.get("health_unreadable")
            status_color = "#DC2626"
        else:
            status = self.i18n.get("health_not_verified")
            status_color = "#D97706"
        detail_lines = [
            self.i18n.get("health_score").format(score=diagnostics.get("scannability_score", 0)),
            self.i18n.get("health_contrast").format(
                ratio=diagnostics.get("contrast_ratio", 0)
            ),
        ]
        if diagnostics.get("warnings"):
            detail_lines.append(self.i18n.get("health_needs_attention"))
        else:
            detail_lines.append(self.i18n.get("health_safe_configuration"))
        if not decoder_available:
            detail_lines.append(self.i18n.get("health_verification_unavailable"))
        self.health_status_label.configure(text=status, text_color=status_color)
        self.health_detail_label.configure(text="\n".join(detail_lines))

    def _mark_qr_stale(self, *_args) -> None:
        if self.current_qr_data is None:
            return
        self.current_qr_data = None
        self._last_diagnostics = None
        self._set_output_actions_enabled(False)
        self.copy_status_label.configure(text="")
        self._set_health_idle(stale=True)

    def _save_qr(self, file_format: str) -> None:
        if self.current_qr_image is None or self.current_qr_data is None:
            messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
            return
        timestamp = get_timestamp_string()
        default_name = f"qrcode_{timestamp}"
        file_type_map = {
            "png": ("PNG files", "*.png"),
            "jpeg": ("JPEG files", "*.jpg"),
            "svg": ("SVG files", "*.svg"),
            "webp": ("WebP files", "*.webp"),
        }
        extension_map = {"png": ".png", "jpeg": ".jpg", "svg": ".svg", "webp": ".webp"}
        file_path = filedialog.asksaveasfilename(
            defaultextension=extension_map[file_format],
            filetypes=[file_type_map[file_format]],
            initialfile=default_name,
        )
        if not file_path:
            return
        try:
            image = self._create_qr_image(self.current_qr_data)
            design = self._current_design_options()
            if file_format == "png":
                self.qr_engine.save_as_png(image, file_path)
            elif file_format == "jpeg":
                self.qr_engine.save_as_jpeg(image, file_path, back_color=self.back_color)
            elif file_format == "webp":
                self.qr_engine.save_as_webp(image, file_path)
            else:
                self.qr_engine.save_as_svg(
                    data=self.current_qr_data,
                    file_path=file_path,
                    fill_color=self.fill_color,
                    back_color=self.back_color,
                    box_size=self.box_size_var.get(),
                    border=self.border_var.get(),
                    error_correction=self.error_correction_var.get(),
                    logo_path=self.logo_path,
                    **design,
                )
            self.config_manager.set("app", "default_export_format", file_format)
            messagebox.showinfo(
                self.i18n.get("msg_success"),
                f"{self.i18n.get('msg_file_saved')}{file_path}",
            )
        except (DataOverflowError, OSError, RuntimeError, ValueError) as save_error:
            messagebox.showerror(self.i18n.get("msg_error"), str(save_error))

    def _copy_qr_data(self) -> None:
        if not self.current_qr_data:
            return
        self.clipboard_clear()
        self.clipboard_append(self.current_qr_data)
        self.update()
        self.copy_status_label.configure(text=self.i18n.get("msg_data_copied"))

    def _persist_qr_defaults(self) -> None:
        design = self._current_design_options()
        self.config_manager.update_section(
            "qr_defaults",
            {
                "box_size": self.box_size_var.get(),
                "border": self.border_var.get(),
                "error_correction": self.error_correction_var.get(),
                "fill_color": self.fill_color,
                "back_color": self.back_color,
                "module_style": design["module_style"],
                "eye_style": design["eye_style"],
                "eye_fill_color": self.eye_fill_color,
                "eye_color_matches_qr": self.eye_color_matches_var.get(),
                "gradient_type": design["gradient_type"] or "none",
                "gradient_color": self.gradient_color,
                "logo_shape": design["logo_shape"],
            },
        )

    def _save_current_defaults(self) -> None:
        self._persist_qr_defaults()
        self.copy_status_label.configure(text=self.i18n.get("msg_defaults_saved"))

    def _handle_generate_shortcut(self, _event) -> str:
        self._generate_qr()
        return "break"

    def _on_language_change(self, selected_language: str) -> None:
        choices = self._current_choice_keys()
        language_code = selected_language.lower()
        self.i18n.load_language(language_code)
        self.config_manager.set("app", "language", language_code)
        self._build_option_label_maps()
        self._rebuild_tabview()
        self._refresh_ui_texts(choices)

    def _on_theme_change(self, selected_theme: str) -> None:
        ctk.set_appearance_mode(selected_theme)
        self.config_manager.set("app", "theme", selected_theme)

    def _current_choice_keys(self) -> dict[str, str]:
        return {
            "module": self._key_for_display("module", self.module_style_var.get(), "square"),
            "eye": self._key_for_display("eye", self.eye_style_var.get(), "square"),
            "gradient": self._key_for_display(
                "gradient", self.gradient_type_var.get(), "none"
            ),
            "logo": self._key_for_display("logo", self.logo_shape_var.get(), "square"),
            "preset": self._key_for_display("preset", self.preset_var.get(), "custom"),
        }

    def _rebuild_tabview(self) -> None:
        saved_url_text = self.url_entry.get()
        saved_text_content = self.text_input.get("1.0", "end-1c")
        saved_vcard_values = {field_name: entry.get() for field_name, entry in self.vcard_entries.items()}
        saved_wifi_ssid = self.wifi_ssid_entry.get()
        saved_wifi_password = self.wifi_password_entry.get()
        saved_wifi_encryption = self.wifi_encryption_var.get()
        saved_wifi_hidden = self.wifi_hidden_var.get()
        active_tab = self._get_active_tab_name()
        self.tabview.destroy()
        self._build_tabview()
        if saved_url_text:
            self.url_entry.insert(0, saved_url_text)
        if saved_text_content:
            self.text_input.insert("1.0", saved_text_content)
        for field_name, value in saved_vcard_values.items():
            if value:
                self.vcard_entries[field_name].insert(0, value)
        if saved_wifi_ssid:
            self.wifi_ssid_entry.insert(0, saved_wifi_ssid)
        if saved_wifi_password:
            self.wifi_password_entry.insert(0, saved_wifi_password)
        self.wifi_encryption_var.set(saved_wifi_encryption)
        self.wifi_hidden_var.set(saved_wifi_hidden)
        self.tabview.set(self._stored_tab_names[active_tab])

    def _refresh_ui_texts(self, choices: dict[str, str]) -> None:
        self.title(self.i18n.get("app_title"))
        self.language_label.configure(text=self.i18n.get("label_language"))
        self.theme_label.configure(text=self.i18n.get("label_theme"))
        self.url_label.configure(text=self.i18n.get("label_url"))
        self.text_label.configure(text=self.i18n.get("label_text"))
        for label_key, field_name in self.vcard_field_definitions:
            self.vcard_labels[field_name].configure(text=self.i18n.get(label_key))
        self.wifi_ssid_label.configure(text=self.i18n.get("label_ssid"))
        self.wifi_password_label.configure(text=self.i18n.get("label_password"))
        self.wifi_encryption_label.configure(text=self.i18n.get("label_encryption"))
        self.wifi_hidden_label.configure(text=self.i18n.get("label_hidden"))

        self.design_header_label.configure(text=self.i18n.get("label_design"))
        self.preset_label.configure(text=self.i18n.get("label_preset"))
        old_basics = self._stored_design_tab_names["basics"]
        old_style = self._stored_design_tab_names["style"]
        new_basics = self.i18n.get("tab_basics")
        new_style = self.i18n.get("tab_style")
        if old_basics != new_basics:
            self.design_tabview.rename(old_basics, new_basics)
        if old_style != new_style:
            self.design_tabview.rename(old_style, new_style)
        self._stored_design_tab_names = {"basics": new_basics, "style": new_style}

        self.module_style_label.configure(text=self.i18n.get("label_module_style"))
        self.eye_style_label.configure(text=self.i18n.get("label_eye_style"))
        self.eye_color_matches_switch.configure(text=self.i18n.get("label_match_qr_color"))
        self.gradient_label.configure(text=self.i18n.get("label_gradient"))
        self.logo_shape_label.configure(text=self.i18n.get("label_logo_shape"))
        self.module_style_menu.configure(values=list(self._option_label_maps["module"]))
        self.eye_style_menu.configure(values=list(self._option_label_maps["eye"]))
        self.gradient_type_menu.configure(values=list(self._option_label_maps["gradient"]))
        self.logo_shape_menu.configure(values=list(self._option_label_maps["logo"]))
        self.preset_menu.configure(values=list(self._option_label_maps["preset"]))
        self.module_style_var.set(self._display_for_key("module", choices["module"]))
        self.eye_style_var.set(self._display_for_key("eye", choices["eye"]))
        self.gradient_type_var.set(self._display_for_key("gradient", choices["gradient"]))
        self.logo_shape_var.set(self._display_for_key("logo", choices["logo"]))
        self.preset_var.set(self._display_for_key("preset", choices["preset"]))

        self.box_size_label.configure(text=self.i18n.get("label_box_size"))
        self.border_label.configure(text=self.i18n.get("label_border"))
        self.error_correction_label.configure(text=self.i18n.get("label_error_correction"))
        self.logo_button.configure(text=self.i18n.get("btn_select_logo"))
        self.remove_logo_button.configure(text=self.i18n.get("btn_remove_logo"))
        self.fix_contrast_button.configure(text=self.i18n.get("btn_fix_contrast"))
        self.save_defaults_button.configure(text=self.i18n.get("btn_save_defaults"))
        self._update_color_buttons()
        self._check_contrast()

        self.generate_button.configure(text=self.i18n.get("btn_generate"))
        self.save_png_button.configure(text=self.i18n.get("btn_save_png"))
        self.save_jpeg_button.configure(text=self.i18n.get("btn_save_jpeg"))
        self.save_svg_button.configure(text=self.i18n.get("btn_save_svg"))
        self.save_webp_button.configure(text=self.i18n.get("btn_save_webp"))
        self.copy_data_button.configure(text=self.i18n.get("btn_copy_data"))
        self.shortcut_label.configure(text=self.i18n.get("shortcut_generate"))
        self.copy_status_label.configure(text="")

        self.preview_title_label.configure(text=self.i18n.get("label_preview"))
        self.health_title_label.configure(text=self.i18n.get("label_scannability"))
        if self.current_qr_data:
            self._update_health_feedback(self.current_qr_data)
        else:
            self._set_health_idle()

    @staticmethod
    def _adjust_brightness(hex_color: str, amount: int) -> str:
        color = hex_color.lstrip("#")
        try:
            red = max(0, min(255, int(color[0:2], 16) + amount))
            green = max(0, min(255, int(color[2:4], 16) + amount))
            blue = max(0, min(255, int(color[4:6], 16) + amount))
        except ValueError:
            return hex_color
        return f"#{red:02x}{green:02x}{blue:02x}"

    @staticmethod
    def _is_light_color(hex_color: str) -> bool:
        color = hex_color.lstrip("#")
        try:
            red = int(color[0:2], 16)
            green = int(color[2:4], 16)
            blue = int(color[4:6], 16)
        except ValueError:
            return False
        luminance = 0.299 * red + 0.587 * green + 0.114 * blue
        return luminance > 128
