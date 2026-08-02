import pytest
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET

from src.qr_engine import (
    QRCodeEngine,
    calculate_contrast_ratio,
    is_inverted,
    get_relative_luminance
)


class TestQRCodeEngine:
    def setup_method(self):
        self.engine = QRCodeEngine()

    def test_generate_qr_returns_image(self):
        result = self.engine.generate_qr("https://example.com", "#000000", "#FFFFFF", 10, 4, "M")
        assert isinstance(result, Image.Image)

    def test_generate_qr_with_text(self):
        result = self.engine.generate_qr("Hello World", "#000000", "#FFFFFF", 10, 4, "L")
        assert result.size[0] > 0
        assert result.size[1] > 0

    def test_generate_qr_high_error_correction(self):
        result = self.engine.generate_qr("Test", "#FF0000", "#00FF00", 8, 2, "H")
        assert isinstance(result, Image.Image)

    def test_save_as_png(self, tmp_path):
        image = self.engine.generate_qr("Test PNG", "#000000", "#FFFFFF", 10, 4, "M")
        file_path = str(tmp_path / "test.png")
        self.engine.save_as_png(image, file_path)
        assert Path(file_path).exists()

    def test_save_as_jpeg(self, tmp_path):
        image = self.engine.generate_qr("Test JPEG", "#000000", "#FFFFFF", 10, 4, "M")
        file_path = str(tmp_path / "test.jpg")
        self.engine.save_as_jpeg(image, file_path, back_color="#FFFFFF")
        assert Path(file_path).exists()

    def test_save_as_svg_contains_custom_colors(self, tmp_path):
        file_path = str(tmp_path / "test.svg")
        fill_color = "#123456"
        back_color = "#FEDCBA"
        self.engine.save_as_svg("Test SVG Colors", file_path, fill_color, back_color, 10, 4, "M")
        assert Path(file_path).exists()

        tree = ET.parse(file_path)
        root = tree.getroot()

        # Verify background rect exists and has fill=back_color
        rects = [e for e in root.iter() if str(e.tag).endswith("rect")]
        assert len(rects) >= 1
        assert rects[0].attrib.get("fill") == back_color

        # Verify path element has fill=fill_color
        paths = [e for e in root.iter() if str(e.tag).endswith("path")]
        assert len(paths) >= 1
        assert paths[0].attrib.get("fill") == fill_color

    def test_generate_qr_with_logo(self, tmp_path):
        logo_path = str(tmp_path / "logo.png")
        logo_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        logo_img.save(logo_path)

        result = self.engine.generate_qr(
            "Test Logo", "#000000", "#FFFFFF", 10, 4, "M", logo_path=logo_path
        )
        assert isinstance(result, Image.Image)

    def test_contrast_ratio_calculation(self):
        ratio_max = calculate_contrast_ratio("#000000", "#FFFFFF")
        assert ratio_max > 20.0

        ratio_low = calculate_contrast_ratio("#777777", "#888888")
        assert ratio_low < 2.0

    def test_is_inverted_detection(self):
        assert is_inverted("#FFFFFF", "#000000") is True
        assert is_inverted("#000000", "#FFFFFF") is False

