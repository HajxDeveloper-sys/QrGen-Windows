import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk
from pathlib import Path
import sys
import ctypes

from src.config_manager import ConfigManager
from src.i18n import I18nManager
from src.qr_engine import QRCodeEngine, calculate_contrast_ratio, is_inverted
from src.wifi_engine import WiFiQREngine
from src.vcard_engine import VCardEngine
from src.utils import validate_url, get_timestamp_string


class QRCodeGeneratorApp(ctk.CTk):

    APPMODEL_ID = "QRCodeGenerator.App.1.0"

    def __init__(self, base_path: Path = Path(".")):
        super().__init__()

        self.base_path = base_path
        self.config_manager = ConfigManager(str(base_path / "config.toml"))
        self.i18n = I18nManager(
            locale_dir=str(base_path / "locale"),
            default_language=self.config_manager.get("app", "language", "tr")
        )

        self.qr_engine = QRCodeEngine()
        self.wifi_engine = WiFiQREngine()
        self.vcard_engine = VCardEngine()

        self.current_qr_image = None
        self.current_qr_data = None
        self.logo_path = None

        self.fill_color = self.config_manager.get("qr_defaults", "fill_color", "#000000")
        self.back_color = self.config_manager.get("qr_defaults", "back_color", "#FFFFFF")

        self._setup_taskbar_icon()
        self._setup_theme()
        self._setup_window()
        self._build_ui()

    def _setup_taskbar_icon(self):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APPMODEL_ID)
        except Exception:
            pass

    def _setup_theme(self):
        theme = self.config_manager.get("app", "theme", "dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

    def _setup_window(self):
        self.title(self.i18n.get("app_title"))
        self.geometry("1100x750")
        self.minsize(1000, 700)

        self._apply_window_icon()

    def _apply_window_icon(self):
        icon_ico_path = self.base_path / "assets" / "icon.ico"
        icon_png_path = self.base_path / "assets" / "icon.png"

        if icon_ico_path.exists():
            self.iconbitmap(str(icon_ico_path))

        if icon_png_path.exists():
            try:
                icon_image = ImageTk.PhotoImage(Image.open(str(icon_png_path)))
                self.wm_iconphoto(True, icon_image)
                self._taskbar_icon_ref = icon_image
            except Exception:
                pass

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, corner_radius=15)
        self.left_frame.grid(row=0, column=0, padx=(15, 7), pady=15, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self._build_settings_bar()
        self._build_tabview()
        self._build_customization_panel()
        self._build_action_buttons()

    def _build_settings_bar(self):
        self.settings_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.settings_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.language_label = ctk.CTkLabel(self.settings_frame, text=self.i18n.get("label_language"))
        self.language_label.grid(row=0, column=0, padx=(5, 5))

        self.language_var = ctk.StringVar(value=self.config_manager.get("app", "language", "tr").upper())
        self.language_selector = ctk.CTkSegmentedButton(
            self.settings_frame,
            values=["TR", "EN"],
            variable=self.language_var,
            command=self._on_language_change
        )
        self.language_selector.grid(row=0, column=1, padx=5)

        self.theme_label = ctk.CTkLabel(self.settings_frame, text=self.i18n.get("label_theme"))
        self.theme_label.grid(row=0, column=2, padx=(20, 5))

        self.theme_var = ctk.StringVar(value=self.config_manager.get("app", "theme", "dark"))
        self.theme_selector = ctk.CTkSegmentedButton(
            self.settings_frame,
            values=["dark", "light"],
            variable=self.theme_var,
            command=self._on_theme_change
        )
        self.theme_selector.grid(row=0, column=3, padx=5)

    def _build_tabview(self):
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

    def _build_url_tab(self):
        self.tab_url.grid_columnconfigure(0, weight=1)

        self.url_label = ctk.CTkLabel(self.tab_url, text=self.i18n.get("label_url"), font=ctk.CTkFont(size=14, weight="bold"))
        self.url_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")

        self.url_entry = ctk.CTkEntry(self.tab_url, placeholder_text="https://example.com", height=40)
        self.url_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

    def _build_text_tab(self):
        self.tab_text.grid_columnconfigure(0, weight=1)
        self.tab_text.grid_rowconfigure(1, weight=1)

        self.text_label = ctk.CTkLabel(self.tab_text, text=self.i18n.get("label_text"), font=ctk.CTkFont(size=14, weight="bold"))
        self.text_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")

        self.text_input = ctk.CTkTextbox(self.tab_text, height=120)
        self.text_input.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

    def _build_vcard_tab(self):
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

        self.vcard_labels = {}
        self.vcard_entries = {}

        for row_index, (label_key, field_name) in enumerate(self.vcard_field_definitions):
            label = ctk.CTkLabel(self.tab_vcard, text=self.i18n.get(label_key))
            label.grid(row=row_index, column=0, padx=(10, 5), pady=3, sticky="w")
            self.vcard_labels[field_name] = label

            entry = ctk.CTkEntry(self.tab_vcard, height=32)
            entry.grid(row=row_index, column=1, padx=(5, 10), pady=3, sticky="ew")
            self.vcard_entries[field_name] = entry

    def _build_wifi_tab(self):
        self.tab_wifi.grid_columnconfigure(1, weight=1)

        self.wifi_ssid_label = ctk.CTkLabel(self.tab_wifi, text=self.i18n.get("label_ssid"))
        self.wifi_ssid_label.grid(row=0, column=0, padx=(10, 5), pady=(15, 5), sticky="w")
        self.wifi_ssid_entry = ctk.CTkEntry(self.tab_wifi, height=35)
        self.wifi_ssid_entry.grid(row=0, column=1, padx=(5, 10), pady=(15, 5), sticky="ew")

        self.wifi_password_label = ctk.CTkLabel(self.tab_wifi, text=self.i18n.get("label_password"))
        self.wifi_password_label.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        self.wifi_password_entry = ctk.CTkEntry(self.tab_wifi, height=35, show="*")
        self.wifi_password_entry.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="ew")

        self.wifi_encryption_label = ctk.CTkLabel(self.tab_wifi, text=self.i18n.get("label_encryption"))
        self.wifi_encryption_label.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="w")

        encryption_values = ["WPA", "WPA2", "WPA3", "WEP", "WPA-Enterprise", "WPS", "nopass"]
        self.wifi_encryption_var = ctk.StringVar(value="WPA")
        self.wifi_encryption_menu = ctk.CTkOptionMenu(
            self.tab_wifi,
            values=encryption_values,
            variable=self.wifi_encryption_var,
            height=35
        )
        self.wifi_encryption_menu.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="ew")

        self.wifi_hidden_label = ctk.CTkLabel(self.tab_wifi, text=self.i18n.get("label_hidden"))
        self.wifi_hidden_label.grid(row=3, column=0, padx=(10, 5), pady=5, sticky="w")
        self.wifi_hidden_var = ctk.BooleanVar(value=False)
        self.wifi_hidden_switch = ctk.CTkSwitch(
            self.tab_wifi,
            text="",
            variable=self.wifi_hidden_var
        )
        self.wifi_hidden_switch.grid(row=3, column=1, padx=(5, 10), pady=5, sticky="w")

    def _build_customization_panel(self):
        self.custom_frame = ctk.CTkFrame(self.left_frame, corner_radius=10)
        self.custom_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.custom_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.fill_color_button = ctk.CTkButton(
            self.custom_frame,
            text=self.i18n.get("label_fill_color"),
            command=self._pick_fill_color,
            fg_color=self.fill_color,
            hover_color=self._adjust_brightness(self.fill_color, 30),
            height=35
        )
        self.fill_color_button.grid(row=0, column=0, padx=5, pady=8, sticky="ew")

        self.back_color_button = ctk.CTkButton(
            self.custom_frame,
            text=self.i18n.get("label_back_color"),
            command=self._pick_back_color,
            fg_color=self.back_color if self.back_color != "#FFFFFF" else "#E0E0E0",
            hover_color=self._adjust_brightness(self.back_color, -30) if self.back_color != "#FFFFFF" else "#D0D0D0",
            text_color="#000000" if self.back_color == "#FFFFFF" else "#FFFFFF",
            height=35
        )
        self.back_color_button.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        self.box_size_label = ctk.CTkLabel(self.custom_frame, text=self.i18n.get("label_box_size"))
        self.box_size_label.grid(row=1, column=0, padx=5, pady=(5, 0), sticky="w")
        self.box_size_var = ctk.IntVar(value=self.config_manager.get("qr_defaults", "box_size", 10))
        self.box_size_slider = ctk.CTkSlider(self.custom_frame, from_=5, to=20, number_of_steps=15, variable=self.box_size_var)
        self.box_size_slider.grid(row=2, column=0, padx=5, pady=(0, 5), sticky="ew")
        self.box_size_value_label = ctk.CTkLabel(self.custom_frame, textvariable=self.box_size_var)
        self.box_size_value_label.grid(row=2, column=0, padx=5, pady=(0, 5), sticky="e")

        self.border_label = ctk.CTkLabel(self.custom_frame, text=self.i18n.get("label_border"))
        self.border_label.grid(row=1, column=1, padx=5, pady=(5, 0), sticky="w")
        self.border_var = ctk.IntVar(value=self.config_manager.get("qr_defaults", "border", 4))
        self.border_slider = ctk.CTkSlider(self.custom_frame, from_=1, to=10, number_of_steps=9, variable=self.border_var)
        self.border_slider.grid(row=2, column=1, padx=5, pady=(0, 5), sticky="ew")
        self.border_value_label = ctk.CTkLabel(self.custom_frame, textvariable=self.border_var)
        self.border_value_label.grid(row=2, column=1, padx=5, pady=(0, 5), sticky="e")

        self.error_correction_label = ctk.CTkLabel(self.custom_frame, text=self.i18n.get("label_error_correction"))
        self.error_correction_label.grid(row=1, column=2, padx=5, pady=(5, 0), sticky="w")
        self.error_correction_var = ctk.StringVar(value=self.config_manager.get("qr_defaults", "error_correction", "M"))
        self.error_correction_menu = ctk.CTkOptionMenu(
            self.custom_frame,
            values=["L", "M", "Q", "H"],
            variable=self.error_correction_var,
            height=30
        )
        self.error_correction_menu.grid(row=2, column=2, padx=5, pady=(0, 5), sticky="ew")

        self.logo_button = ctk.CTkButton(
            self.custom_frame,
            text=self.i18n.get("btn_select_logo"),
            command=self._select_logo,
            height=35
        )
        self.logo_button.grid(row=0, column=2, padx=5, pady=8, sticky="ew")

        self.remove_logo_button = ctk.CTkButton(
            self.custom_frame,
            text=self.i18n.get("btn_remove_logo"),
            command=self._remove_logo,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            height=35,
            state="disabled"
        )
        self.remove_logo_button.grid(row=0, column=3, padx=5, pady=8, sticky="ew")

        self.logo_status_label = ctk.CTkLabel(self.custom_frame, text="", font=ctk.CTkFont(size=11))
        self.logo_status_label.grid(row=1, column=3, columnspan=1, padx=5, pady=0, sticky="w")

        self.contrast_warning_label = ctk.CTkLabel(
            self.custom_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#EF4444",
            wraplength=400
        )
        self.contrast_warning_label.grid(row=3, column=0, columnspan=3, padx=5, pady=(5, 5), sticky="w")

        self.fix_contrast_button = ctk.CTkButton(
            self.custom_frame,
            text=self.i18n.get("btn_fix_contrast"),
            command=self._fix_color_contrast,
            height=32,
            fg_color="#D97706",
            hover_color="#B45309"
        )
        self.fix_contrast_button.grid(row=3, column=3, padx=5, pady=(5, 5), sticky="ew")

        self._check_contrast()

    def _build_action_buttons(self):
        self.action_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.action_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.generate_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_generate"),
            command=self._generate_qr,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8"
        )
        self.generate_button.grid(row=0, column=0, columnspan=4, padx=5, pady=(5, 8), sticky="ew")

        self.save_png_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_save_png"),
            command=lambda: self._save_qr("png"),
            height=36,
            fg_color="#059669",
            hover_color="#047857"
        )
        self.save_png_button.grid(row=1, column=0, padx=3, pady=3, sticky="ew")

        self.save_jpeg_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_save_jpeg"),
            command=lambda: self._save_qr("jpeg"),
            height=36,
            fg_color="#D97706",
            hover_color="#B45309"
        )
        self.save_jpeg_button.grid(row=1, column=1, padx=3, pady=3, sticky="ew")

        self.save_svg_button = ctk.CTkButton(
            self.action_frame,
            text=self.i18n.get("btn_save_svg"),
            command=lambda: self._save_qr("svg"),
            height=36,
            fg_color="#7C3AED",
            hover_color="#6D28D9"
        )
        self.save_svg_button.grid(row=1, column=2, padx=3, pady=3, sticky="ew")

    def _build_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, corner_radius=15)
        self.right_frame.grid(row=0, column=1, padx=(7, 15), pady=15, sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.preview_title_label = ctk.CTkLabel(
            self.right_frame,
            text=self.i18n.get("label_preview"),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.preview_title_label.grid(row=0, column=0, padx=15, pady=(15, 5))

        self.preview_canvas_frame = ctk.CTkFrame(self.right_frame, corner_radius=12, fg_color=("gray92", "gray17"))
        self.preview_canvas_frame.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.preview_canvas_frame.grid_rowconfigure(0, weight=1)
        self.preview_canvas_frame.grid_columnconfigure(0, weight=1)

        self.preview_image_label = ctk.CTkLabel(self.preview_canvas_frame, text="")
        self.preview_image_label.grid(row=0, column=0, padx=10, pady=10)

        self._show_placeholder_preview()

    def _show_placeholder_preview(self):
        placeholder_size = 300
        placeholder = Image.new("RGBA", (placeholder_size, placeholder_size), (200, 200, 200, 50))
        self._display_preview_image(placeholder)

    def _display_preview_image(self, pil_image: Image.Image):
        preview_size = 350
        image_copy = pil_image.copy()
        image_copy.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)
        self.preview_ctk_image = ctk.CTkImage(light_image=image_copy, dark_image=image_copy, size=image_copy.size)
        self.preview_image_label.configure(image=self.preview_ctk_image, text="")

    def _check_contrast(self):
        ratio = calculate_contrast_ratio(self.fill_color, self.back_color)
        inverted = is_inverted(self.fill_color, self.back_color)

        if inverted:
            self.contrast_warning_label.configure(
                text=self.i18n.get("warn_inverted"),
                text_color="#EF4444"
            )
            self.fix_contrast_button.grid()
        elif ratio < 4.0:
            self.contrast_warning_label.configure(
                text=f"{self.i18n.get('warn_low_contrast')} (1:{ratio:.1f})",
                text_color="#F59E0B"
            )
            self.fix_contrast_button.grid()
        else:
            self.contrast_warning_label.configure(text="")
            self.fix_contrast_button.grid_remove()

    def _fix_color_contrast(self):
        inverted = is_inverted(self.fill_color, self.back_color)
        if inverted:
            self.fill_color, self.back_color = self.back_color, self.fill_color
        else:
            self.fill_color = "#000000"
            self.back_color = "#FFFFFF"

        self._update_color_buttons()
        self._check_contrast()
        if self.current_qr_data:
            self._generate_qr()

    def _update_color_buttons(self):
        self.fill_color_button.configure(
            fg_color=self.fill_color,
            hover_color=self._adjust_brightness(self.fill_color, 30)
        )
        display_fg = self.back_color if self.back_color != "#FFFFFF" else "#E0E0E0"
        display_hover = self._adjust_brightness(self.back_color, -30) if self.back_color != "#FFFFFF" else "#D0D0D0"
        text_clr = "#000000" if self._is_light_color(self.back_color) else "#FFFFFF"
        self.back_color_button.configure(
            fg_color=display_fg,
            hover_color=display_hover,
            text_color=text_clr
        )

    def _pick_fill_color(self):
        color = colorchooser.askcolor(initialcolor=self.fill_color, title=self.i18n.get("label_fill_color"))
        if color and color[1]:
            self.fill_color = color[1]
            self._update_color_buttons()
            self._check_contrast()
            if self.current_qr_data:
                self._generate_qr()

    def _pick_back_color(self):
        color = colorchooser.askcolor(initialcolor=self.back_color, title=self.i18n.get("label_back_color"))
        if color and color[1]:
            self.back_color = color[1]
            self._update_color_buttons()
            self._check_contrast()
            if self.current_qr_data:
                self._generate_qr()

    def _select_logo(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.ico")]
        )
        if file_path:
            self.logo_path = file_path
            logo_name = Path(file_path).name
            self.logo_status_label.configure(text=f"📎 {logo_name}")
            self.remove_logo_button.configure(state="normal")
            if self.current_qr_data:
                self._generate_qr()

    def _remove_logo(self):
        self.logo_path = None
        self.logo_status_label.configure(text="")
        self.remove_logo_button.configure(state="disabled")
        if self.current_qr_data:
            self._generate_qr()

    def _get_active_tab_name(self) -> str:
        current_tab = self.tabview.get()
        tab_mapping = {
            self._stored_tab_names["url"]: "url",
            self._stored_tab_names["text"]: "text",
            self._stored_tab_names["vcard"]: "vcard",
            self._stored_tab_names["wifi"]: "wifi",
        }
        return tab_mapping.get(current_tab, "url")

    def _generate_qr(self):
        active_tab = self._get_active_tab_name()
        qr_data = ""

        if active_tab == "url":
            qr_data = self.url_entry.get().strip()
            if not qr_data:
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
                return
            if not validate_url(qr_data):
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_invalid_url"))
                return

        elif active_tab == "text":
            qr_data = self.text_input.get("1.0", "end-1c").strip()
            if not qr_data:
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
                return

        elif active_tab == "vcard":
            first_name = self.vcard_entries["first_name"].get().strip()
            last_name = self.vcard_entries["last_name"].get().strip()
            if not first_name and not last_name:
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
                return
            qr_data = self.vcard_engine.generate_vcard_string(
                first_name=first_name,
                last_name=last_name,
                phone=self.vcard_entries["phone"].get().strip(),
                email=self.vcard_entries["email"].get().strip(),
                company=self.vcard_entries["company"].get().strip(),
                title=self.vcard_entries["title"].get().strip(),
                website=self.vcard_entries["website"].get().strip(),
                address=self.vcard_entries["address"].get().strip(),
            )

        elif active_tab == "wifi":
            ssid = self.wifi_ssid_entry.get().strip()
            if not ssid:
                messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
                return
            password = self.wifi_password_entry.get().strip()
            encryption = self.wifi_encryption_var.get()
            hidden = self.wifi_hidden_var.get()
            qr_data = self.wifi_engine.generate_wifi_string(ssid, password, encryption, hidden)

        try:
            self.current_qr_data = qr_data
            self.current_qr_image = self.qr_engine.generate_qr(
                data=qr_data,
                fill_color=self.fill_color,
                back_color=self.back_color,
                box_size=self.box_size_var.get(),
                border=self.border_var.get(),
                error_correction=self.error_correction_var.get(),
                logo_path=self.logo_path
            )
            self._display_preview_image(self.current_qr_image)
        except Exception as generation_error:
            messagebox.showerror(self.i18n.get("msg_error"), str(generation_error))

    def _save_qr(self, file_format: str):
        if self.current_qr_image is None and file_format != "svg":
            messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
            return
        if file_format == "svg" and self.current_qr_data is None:
            messagebox.showwarning(self.i18n.get("msg_error"), self.i18n.get("msg_empty_input"))
            return

        timestamp = get_timestamp_string()
        default_name = f"qrcode_{timestamp}"

        file_type_map = {
            "png": ("PNG files", "*.png"),
            "jpeg": ("JPEG files", "*.jpg"),
            "svg": ("SVG files", "*.svg"),
        }
        extension_map = {"png": ".png", "jpeg": ".jpg", "svg": ".svg"}

        file_path = filedialog.asksaveasfilename(
            defaultextension=extension_map[file_format],
            filetypes=[file_type_map[file_format]],
            initialfile=default_name
        )

        if not file_path:
            return

        try:
            if self.current_qr_data:
                self.current_qr_image = self.qr_engine.generate_qr(
                    data=self.current_qr_data,
                    fill_color=self.fill_color,
                    back_color=self.back_color,
                    box_size=self.box_size_var.get(),
                    border=self.border_var.get(),
                    error_correction=self.error_correction_var.get(),
                    logo_path=self.logo_path
                )

            if file_format == "png":
                self.qr_engine.save_as_png(self.current_qr_image, file_path)
            elif file_format == "jpeg":
                self.qr_engine.save_as_jpeg(self.current_qr_image, file_path, back_color=self.back_color)
            elif file_format == "svg":
                self.qr_engine.save_as_svg(
                    data=self.current_qr_data,
                    file_path=file_path,
                    fill_color=self.fill_color,
                    back_color=self.back_color,
                    box_size=self.box_size_var.get(),
                    border=self.border_var.get(),
                    error_correction=self.error_correction_var.get(),
                    logo_path=self.logo_path
                )

            messagebox.showinfo(
                self.i18n.get("msg_success"),
                f"{self.i18n.get('msg_file_saved')}{file_path}"
            )
        except Exception as save_error:
            messagebox.showerror(self.i18n.get("msg_error"), str(save_error))

    def _on_language_change(self, selected_language: str):
        language_code = selected_language.lower()
        self.i18n.load_language(language_code)
        self.config_manager.set("app", "language", language_code)
        self._rebuild_tabview()
        self._refresh_ui_texts()

    def _on_theme_change(self, selected_theme: str):
        ctk.set_appearance_mode(selected_theme)
        self.config_manager.set("app", "theme", selected_theme)

    def _rebuild_tabview(self):
        saved_url_text = self.url_entry.get()
        saved_text_content = self.text_input.get("1.0", "end-1c")

        saved_vcard_values = {}
        for field_name, entry in self.vcard_entries.items():
            saved_vcard_values[field_name] = entry.get()

        saved_wifi_ssid = self.wifi_ssid_entry.get()
        saved_wifi_password = self.wifi_password_entry.get()
        saved_wifi_encryption = self.wifi_encryption_var.get()
        saved_wifi_hidden = self.wifi_hidden_var.get()

        active_tab = self._get_active_tab_name()

        self.tabview.destroy()

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

        if saved_url_text:
            self.url_entry.insert(0, saved_url_text)
        if saved_text_content:
            self.text_input.insert("1.0", saved_text_content)
        for field_name, value in saved_vcard_values.items():
            if value and field_name in self.vcard_entries:
                self.vcard_entries[field_name].insert(0, value)
        if saved_wifi_ssid:
            self.wifi_ssid_entry.insert(0, saved_wifi_ssid)
        if saved_wifi_password:
            self.wifi_password_entry.insert(0, saved_wifi_password)
        self.wifi_encryption_var.set(saved_wifi_encryption)
        self.wifi_hidden_var.set(saved_wifi_hidden)

        tab_to_name = {
            "url": self.i18n.get("tab_url"),
            "text": self.i18n.get("tab_text"),
            "vcard": self.i18n.get("tab_vcard"),
            "wifi": self.i18n.get("tab_wifi"),
        }
        if active_tab in tab_to_name:
            self.tabview.set(tab_to_name[active_tab])

    def _refresh_ui_texts(self):
        self.title(self.i18n.get("app_title"))

        self.language_label.configure(text=self.i18n.get("label_language"))
        self.theme_label.configure(text=self.i18n.get("label_theme"))

        self.url_label.configure(text=self.i18n.get("label_url"))
        self.text_label.configure(text=self.i18n.get("label_text"))

        for label_key, field_name in self.vcard_field_definitions:
            if field_name in self.vcard_labels:
                self.vcard_labels[field_name].configure(text=self.i18n.get(label_key))

        self.wifi_ssid_label.configure(text=self.i18n.get("label_ssid"))
        self.wifi_password_label.configure(text=self.i18n.get("label_password"))
        self.wifi_encryption_label.configure(text=self.i18n.get("label_encryption"))
        self.wifi_hidden_label.configure(text=self.i18n.get("label_hidden"))

        self.fill_color_button.configure(text=self.i18n.get("label_fill_color"))
        self.back_color_button.configure(text=self.i18n.get("label_back_color"))
        self.box_size_label.configure(text=self.i18n.get("label_box_size"))
        self.border_label.configure(text=self.i18n.get("label_border"))
        self.error_correction_label.configure(text=self.i18n.get("label_error_correction"))
        self.logo_button.configure(text=self.i18n.get("btn_select_logo"))
        self.remove_logo_button.configure(text=self.i18n.get("btn_remove_logo"))
        self.fix_contrast_button.configure(text=self.i18n.get("btn_fix_contrast"))
        self._check_contrast()

        self.generate_button.configure(text=self.i18n.get("btn_generate"))
        self.save_png_button.configure(text=self.i18n.get("btn_save_png"))
        self.save_jpeg_button.configure(text=self.i18n.get("btn_save_jpeg"))
        self.save_svg_button.configure(text=self.i18n.get("btn_save_svg"))

        self.preview_title_label.configure(text=self.i18n.get("label_preview"))

    @staticmethod
    def _adjust_brightness(hex_color: str, amount: int) -> str:
        hex_color = hex_color.lstrip("#")
        red = max(0, min(255, int(hex_color[0:2], 16) + amount))
        green = max(0, min(255, int(hex_color[2:4], 16) + amount))
        blue = max(0, min(255, int(hex_color[4:6], 16) + amount))
        return f"#{red:02x}{green:02x}{blue:02x}"

    @staticmethod
    def _is_light_color(hex_color: str) -> bool:
        hex_color = hex_color.lstrip("#")
        red = int(hex_color[0:2], 16)
        green = int(hex_color[2:4], 16)
        blue = int(hex_color[4:6], 16)
        luminance = (0.299 * red + 0.587 * green + 0.114 * blue)
        return luminance > 128
