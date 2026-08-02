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

        rects = [e for e in root.iter() if str(e.tag).endswith("rect")]
        assert len(rects) >= 1
        assert rects[0].attrib.get("fill") == back_color

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

    def test_save_as_svg_attributes_and_centering(self, tmp_path):
        file_path = str(tmp_path / "test_centered.svg")
        fill_color = "#1E3A8A"
        back_color = "#EFF6FF"
        self.engine.save_as_svg("Test Centered SVG", file_path, fill_color, back_color, 10, 4, "M")
        assert Path(file_path).exists()

        tree = ET.parse(file_path)
        root = tree.getroot()

        assert "width" in root.attrib and root.attrib["width"] == "100%"
        assert "height" in root.attrib and root.attrib["height"] == "100%"
        assert root.attrib.get("preserveAspectRatio") == "xMidYMid meet"
        assert root.attrib.get("shape-rendering") == "crispEdges"
        assert "viewBox" in root.attrib
        assert "margin: auto" in root.attrib.get("style", "")

        rects = [e for e in root.iter() if str(e.tag).endswith("rect")]
        bg_rect = rects[0]
        assert bg_rect.attrib.get("fill") == back_color
        assert bg_rect.attrib.get("x") == "0"
        assert bg_rect.attrib.get("y") == "0"
        assert bg_rect.attrib.get("width") != "100%"


    def test_save_as_svg_with_logo(self, tmp_path):
        logo_path = str(tmp_path / "logo.png")
        logo_img = Image.new("RGBA", (50, 50), (0, 128, 255, 255))
        logo_img.save(logo_path)

        svg_path = str(tmp_path / "test_logo.svg")
        self.engine.save_as_svg(
            "SVG Logo Test", svg_path, "#000000", "#FFFFFF", 10, 4, "M", logo_path=logo_path
        )
        assert Path(svg_path).exists()

        tree = ET.parse(svg_path)
        root = tree.getroot()
        images = [e for e in root.iter() if str(e.tag).endswith("image")]
        assert len(images) == 1
        img_elem = images[0]
        assert "href" in img_elem.attrib
        assert img_elem.attrib.get("{http://www.w3.org/1999/xlink}href") is not None

    def test_scannability_png_and_jpeg(self, tmp_path):
        import zxingcpp

        test_data = "https://github.com/qrcode"
        png_path = str(tmp_path / "scan.png")
        jpg_path = str(tmp_path / "scan.jpg")

        img = self.engine.generate_qr(test_data, "#1E3A8A", "#EFF6FF", 10, 4, "M")
        self.engine.save_as_png(img, png_path)
        self.engine.save_as_jpeg(img, jpg_path, back_color="#EFF6FF")

        read_png = zxingcpp.read_barcode(Image.open(png_path))
        read_jpg = zxingcpp.read_barcode(Image.open(jpg_path))

        assert read_png is not None and read_png.text == test_data
        assert read_jpg is not None and read_jpg.text == test_data

    def test_contrast_ratio_calculation(self):
        ratio_max = calculate_contrast_ratio("#000000", "#FFFFFF")
        assert ratio_max > 20.0

        ratio_low = calculate_contrast_ratio("#777777", "#888888")
        assert ratio_low < 2.0

    def test_is_inverted_detection(self):
        assert is_inverted("#FFFFFF", "#000000") is True
        assert is_inverted("#000000", "#FFFFFF") is False


