import pytest
from pathlib import Path
from PIL import Image
from src.qr_engine import QRCodeEngine


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
        self.engine.save_as_jpeg(image, file_path)
        assert Path(file_path).exists()

    def test_save_as_svg(self, tmp_path):
        file_path = str(tmp_path / "test.svg")
        self.engine.save_as_svg("Test SVG", file_path, "#000000", "#FFFFFF", 10, 4, "M")
        assert Path(file_path).exists()
