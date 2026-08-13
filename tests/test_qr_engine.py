import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

from src.qr_engine import (
    QRCodeEngine,
    calculate_contrast_ratio,
    get_relative_luminance,
    is_inverted,
    parse_color,
    suggest_optimal_colors,
)


class TestQRCodeEngineBasic:
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


class TestColorAndContrastEngine:
    def test_parse_color_hex(self):
        assert parse_color("#000000") == (0, 0, 0, 255)
        assert parse_color("#FFFFFF") == (255, 255, 255, 255)
        assert parse_color("#FF000080") == (255, 0, 0, 128)
        assert parse_color("#FFF") == (255, 255, 255, 255)

    def test_parse_color_names_and_tuples(self):
        assert parse_color("white") == (255, 255, 255, 255)
        assert parse_color("black") == (0, 0, 0, 255)
        assert parse_color((100, 150, 200)) == (100, 150, 200, 255)
        assert parse_color((10, 20, 30, 40)) == (10, 20, 30, 40)
        assert parse_color("invalid_color_name") == (0, 0, 0, 255)

    def test_luminance_calculation(self):
        lum_white = get_relative_luminance("#FFFFFF")
        lum_black = get_relative_luminance("#000000")
        assert lum_white > 0.99
        assert lum_black < 0.01
        assert lum_white > lum_black

    def test_contrast_ratio_calculation(self):
        ratio_max = calculate_contrast_ratio("#000000", "#FFFFFF")
        assert ratio_max > 20.0

        ratio_low = calculate_contrast_ratio("#777777", "#888888")
        assert ratio_low < 2.0

    def test_is_inverted_detection(self):
        assert is_inverted("#FFFFFF", "#000000") is True
        assert is_inverted("#000000", "#FFFFFF") is False

    def test_suggest_optimal_colors(self):
        fill, back = suggest_optimal_colors("#FFFFFF", "#000000")
        assert fill == "#000000" and back == "#FFFFFF"

        fill2, back2 = suggest_optimal_colors("#777777", "#FFFFFF")
        assert fill2 == "#000000" and back2 == "#FFFFFF"


class TestModuleAndEyeStyles:
    def setup_method(self):
        self.engine = QRCodeEngine()

    @pytest.mark.parametrize("style", ["square", "rounded", "circle", "dots", "gapped"])
    def test_module_styles(self, style):
        img = self.engine.generate_qr(
            "https://github.com", "#000000", "#FFFFFF", box_size=10, border=4, module_style=style
        )
        assert isinstance(img, Image.Image)

    @pytest.mark.parametrize("eye_style", ["square", "rounded", "circle"])
    def test_eye_styles_and_colors(self, eye_style):
        img = self.engine.generate_qr(
            "https://github.com",
            fill_color="#1D4ED8",
            back_color="#F3F4F6",
            box_size=10,
            border=4,
            eye_style=eye_style,
            eye_fill_color="#DC2626"
        )
        assert isinstance(img, Image.Image)


class TestGradients:
    def setup_method(self):
        self.engine = QRCodeEngine()

    @pytest.mark.parametrize("grad_type", ["linear_h", "linear_v", "radial"])
    def test_gradient_qr_generation(self, grad_type):
        img = self.engine.generate_qr(
            "Gradient QR Test",
            fill_color="#1E40AF",
            back_color="#FFFFFF",
            box_size=10,
            border=4,
            gradient_type=grad_type,
            gradient_color="#9333EA"
        )
        assert isinstance(img, Image.Image)


class TestLogoEmbedding:
    def setup_method(self):
        self.engine = QRCodeEngine()

    @pytest.mark.parametrize("shape", ["square", "circle", "rounded"])
    def test_generate_qr_with_logo_shapes(self, tmp_path, shape):
        logo_path = str(tmp_path / f"logo_{shape}.png")
        logo_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        logo_img.save(logo_path)

        result = self.engine.generate_qr(
            "Test Logo Shapes", "#000000", "#FFFFFF", 10, 4, "M", logo_path=logo_path, logo_shape=shape
        )
        assert isinstance(result, Image.Image)

    def test_logo_forces_high_error_correction(self, tmp_path):
        logo_path = str(tmp_path / "logo.png")
        Image.new("RGBA", (50, 50), (0, 0, 255, 255)).save(logo_path)

        diag = self.engine.analyze_scannability(
            "High EC Logo Test", "#000000", "#FFFFFF", error_correction="L", logo_path=logo_path
        )
        assert any("upgraded error correction level to 'H'" in r for r in diag["recommendations"])


class TestExportFormats:
    def setup_method(self):
        self.engine = QRCodeEngine()

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

    def test_save_as_webp(self, tmp_path):
        image = self.engine.generate_qr("Test WebP", "#000000", "#FFFFFF", 10, 4, "M")
        file_path = str(tmp_path / "test.webp")
        self.engine.save_as_webp(image, file_path, quality=90)
        assert Path(file_path).exists()

    def test_to_base64_and_data_uri(self):
        image = self.engine.generate_qr("Test Base64", "#000000", "#FFFFFF", 10, 4, "M")
        b64 = self.engine.to_base64_png(image)
        assert isinstance(b64, str) and len(b64) > 50

        uri = self.engine.to_data_uri(image, "png")
        assert uri.startswith("data:image/png;base64,")

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

    def test_save_as_svg_preserves_advanced_style_visuals(self, tmp_path):
        svg_path = str(tmp_path / "advanced.svg")
        self.engine.save_as_svg(
            "Advanced SVG",
            svg_path,
            "#0F4C81",
            "#F7FBFF",
            module_style="rounded",
            eye_style="circle",
            eye_fill_color="#075985",
            gradient_type="linear_h",
            gradient_color="#0369A1",
            logo_shape="rounded",
        )

        root = ET.parse(svg_path).getroot()
        images = [element for element in root.iter() if str(element.tag).endswith("image")]
        assert len(images) == 1
        assert images[0].attrib["href"].startswith("data:image/png;base64,")

    def test_to_base64_svg(self):
        b64_svg = self.engine.to_base64_svg("Base64 SVG Data", "#000000", "#FFFFFF")
        assert isinstance(b64_svg, str) and len(b64_svg) > 50


class TestScannabilityVerification:
    def setup_method(self):
        self.engine = QRCodeEngine()

    def test_scannability_png_and_jpeg(self, tmp_path):
        test_data = "https://github.com/qrcode"
        png_path = str(tmp_path / "scan.png")
        jpg_path = str(tmp_path / "scan.jpg")

        img = self.engine.generate_qr(test_data, "#1E3A8A", "#EFF6FF", 10, 4, "M")
        self.engine.save_as_png(img, png_path)
        self.engine.save_as_jpeg(img, jpg_path, back_color="#EFF6FF")

        res_png = self.engine.check_scannability(png_path)
        res_jpg = self.engine.check_scannability(jpg_path)

        assert res_png["scannable"] is True
        assert res_png["decoded_text"] == test_data

        assert res_jpg["scannable"] is True
        assert res_jpg["decoded_text"] == test_data

    def test_scannability_with_styled_modules_and_logo(self, tmp_path):
        logo_path = str(tmp_path / "scan_logo.png")
        logo_img = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
        logo_img.save(logo_path)

        test_data = "WIFI:S:MyHomeNetwork;T:WPA;P:SecretPass123;;"
        img = self.engine.generate_qr(
            test_data,
            fill_color="#0F172A",
            back_color="#F8FAFC",
            box_size=12,
            border=4,
            error_correction="H",
            logo_path=logo_path,
            logo_shape="circle",
            module_style="rounded",
            eye_style="rounded"
        )

        res = self.engine.check_scannability(img)
        assert res["scannable"] is True
        assert res["decoded_text"] == test_data

    def test_analyze_scannability_diagnostics(self):
        diag_good = self.engine.analyze_scannability(
            "Diagnostics Test", "#000000", "#FFFFFF", box_size=10, border=4
        )
        assert diag_good["scannability_score"] >= 90
        assert diag_good["is_inverted"] is False
        assert diag_good["contrast_ratio"] > 10.0
        assert len(diag_good["warnings"]) == 0

        diag_bad = self.engine.analyze_scannability(
            "Diagnostics Bad", "#FFFFFF", "#000000", box_size=10, border=2
        )
        assert diag_bad["is_inverted"] is True
        assert len(diag_bad["warnings"]) >= 1

    def test_analyze_scannability_checks_gradient_and_eye_colors(self):
        diagnostics = self.engine.analyze_scannability(
            "Style diagnostics",
            "#000000",
            "#FFFFFF",
            gradient_type="linear_h",
            gradient_color="#999999",
            eye_fill_color="#999999",
            eye_style="circle",
            logo_shape="rounded",
        )

        assert diagnostics["contrast_ratio"] < 4.5
        assert any("Gradient endpoint" in warning for warning in diagnostics["warnings"])
        assert any("Finder eye color" in warning for warning in diagnostics["warnings"])
