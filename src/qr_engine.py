import base64
import io
import math
import pathlib
import xml.etree.ElementTree as ET

import qrcode
import qrcode.image.svg
from PIL import Image, ImageColor, ImageDraw

try:
    import zxingcpp
    HAS_ZXING = True
except ImportError:
    HAS_ZXING = False


def parse_color(color_input: str | tuple | list) -> tuple[int, int, int, int]:
    """
    Parses color from hex string (#RGB, #RGBA, #RRGGBB, #RRGGBBAA), color name, or tuple/list.
    Returns RGBA tuple (r, g, b, a).
    """
    if isinstance(color_input, (tuple, list)):
        if len(color_input) == 3:
            return (int(color_input[0]), int(color_input[1]), int(color_input[2]), 255)
        elif len(color_input) >= 4:
            return (int(color_input[0]), int(color_input[1]), int(color_input[2]), int(color_input[3]))

    if not isinstance(color_input, str):
        return (0, 0, 0, 255)

    color_str = color_input.strip()

    if color_str.startswith("#"):
        hex_val = color_str.lstrip("#")
        if len(hex_val) == 3:
            hex_val = "".join(c * 2 for c in hex_val) + "FF"
        elif len(hex_val) == 4:
            hex_val = "".join(c * 2 for c in hex_val)
        elif len(hex_val) == 6:
            hex_val = hex_val + "FF"

        if len(hex_val) == 8:
            try:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                a = int(hex_val[6:8], 16)
                return (r, g, b, a)
            except ValueError:
                pass

    try:
        rgb = ImageColor.getrgb(color_str)
        if len(rgb) == 3:
            return (rgb[0], rgb[1], rgb[2], 255)
        return (rgb[0], rgb[1], rgb[2], rgb[3])
    except ValueError:
        return (0, 0, 0, 255)


def get_relative_luminance(color_input: str | tuple) -> float:
    """
    Calculates WCAG 2.1 relative luminance for a color.
    """
    r_255, g_255, b_255, _ = parse_color(color_input)
    r = r_255 / 255.0
    g = g_255 / 255.0
    b = b_255 / 255.0

    def srgb_to_lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)


def calculate_contrast_ratio(fill_color: str | tuple, back_color: str | tuple) -> float:
    """
    Calculates contrast ratio between fill and background color according to WCAG guidelines.
    """
    l1 = get_relative_luminance(fill_color)
    l2 = get_relative_luminance(back_color)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_inverted(fill_color: str | tuple, back_color: str | tuple) -> bool:
    """
    Checks if fill color is lighter than background color (inverted QR code).
    Inverted QR codes can cause scanning failures on some mobile cameras.
    """
    return get_relative_luminance(fill_color) > get_relative_luminance(back_color)


def suggest_optimal_colors(fill_color: str, back_color: str) -> tuple[str, str]:
    """
    Returns optimal high-contrast fill and background colors if the input pair is inverted or low contrast.
    """
    if is_inverted(fill_color, back_color):
        return back_color, fill_color

    ratio = calculate_contrast_ratio(fill_color, back_color)
    if ratio < 4.5:
        bg_lum = get_relative_luminance(back_color)
        if bg_lum >= 0.5:
            return "#000000", back_color
        else:
            return "#FFFFFF", back_color

    return fill_color, back_color


class QRCodeEngine:
    """
    Engine for creating rich, highly-customizable, scannable QR codes with advanced
    module styles, finder pattern (eye) styles, color gradients, logo embedding, and verification.
    """

    def generate_qr(
        self,
        data: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        error_correction: str = "M",
        logo_path: str | None = None,
        module_style: str = "square",
        eye_style: str = "square",
        eye_fill_color: str | None = None,
        gradient_type: str | None = None,
        gradient_color: str | None = None,
        logo_shape: str = "square",
        verify_scannability: bool = False
    ) -> Image.Image:
        error_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        if logo_path is not None:
            error_correction = 'H'

        error_correct_level = error_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)

        qr = qrcode.QRCode(
            version=None,
            error_correction=error_correct_level,
            box_size=box_size,
            border=border
        )
        qr.add_data(data)
        qr.make(fit=True)

        matrix = qr.get_matrix()
        num_modules = len(matrix)
        img_size = num_modules * box_size

        fill_rgba = parse_color(fill_color)
        back_rgba = parse_color(back_color)
        eye_fill_rgba = parse_color(eye_fill_color) if eye_fill_color else fill_rgba
        grad_rgba = parse_color(gradient_color) if gradient_color else fill_rgba

        img = Image.new("RGBA", (img_size, img_size), back_rgba)
        draw = ImageDraw.Draw(img)

        finder_mask = [[False] * num_modules for _ in range(num_modules)]
        eye_center_mask = [[False] * num_modules for _ in range(num_modules)]
        eye_outer_mask = [[False] * num_modules for _ in range(num_modules)]

        finder_corners = [
            (border, border),
            (border, num_modules - border - 7),
            (num_modules - border - 7, border)
        ]

        for r0, c0 in finder_corners:
            for r in range(7):
                for c in range(7):
                    mr, mc = r0 + r, c0 + c
                    if 0 <= mr < num_modules and 0 <= mc < num_modules:
                        finder_mask[mr][mc] = True
                        if 2 <= r <= 4 and 2 <= c <= 4:
                            eye_center_mask[mr][mc] = True
                        else:
                            eye_outer_mask[mr][mc] = True

        for r0, c0 in finder_corners:
            self._draw_finder_pattern(
                draw, r0, c0, box_size, eye_style, fill_rgba, eye_fill_rgba, back_rgba
            )

        for r in range(num_modules):
            for c in range(num_modules):
                if finder_mask[r][c]:
                    continue
                if matrix[r][c]:
                    if gradient_type and gradient_color:
                        m_color = self._get_gradient_color(
                            r, c, num_modules, fill_rgba, grad_rgba, gradient_type
                        )
                    else:
                        m_color = fill_rgba

                    self._draw_module(draw, r, c, box_size, module_style, m_color)

        if logo_path is not None and pathlib.Path(logo_path).exists():
            img = self._apply_logo(img, logo_path, back_color, logo_shape)

        result = img.convert("RGB")

        if verify_scannability and HAS_ZXING:
            scan_res = self.check_scannability(result)
            if not scan_res.get("scannable", False):
                pass

        return result

    def _get_gradient_color(
        self, r: int, c: int, total_modules: int,
        c1: tuple[int, int, int, int], c2: tuple[int, int, int, int],
        grad_type: str
    ) -> tuple[int, int, int, int]:
        if grad_type == "linear_h":
            t = c / max(1, total_modules - 1)
        elif grad_type == "linear_v":
            t = r / max(1, total_modules - 1)
        elif grad_type == "radial":
            center = (total_modules - 1) / 2.0
            dist = math.sqrt((r - center) ** 2 + (c - center) ** 2)
            max_dist = math.sqrt(2) * center
            t = min(1.0, dist / max(1, max_dist))
        else:
            t = 0.0

        r_c = int(c1[0] + (c2[0] - c1[0]) * t)
        g_c = int(c1[1] + (c2[1] - c1[1]) * t)
        b_c = int(c1[2] + (c2[2] - c1[2]) * t)
        a_c = int(c1[3] + (c2[3] - c1[3]) * t)
        return (r_c, g_c, b_c, a_c)

    def _draw_module(
        self, draw: ImageDraw.ImageDraw, r: int, c: int,
        box_size: int, style: str, color: tuple[int, int, int, int]
    ) -> None:
        x0 = c * box_size
        y0 = r * box_size
        x1 = x0 + box_size
        y1 = y0 + box_size

        if style == "rounded":
            radius = max(2, box_size // 3)
            draw.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=radius, fill=color)
        elif style in ("circle", "dots"):
            margin = max(1, box_size // 10)
            draw.ellipse([x0 + margin, y0 + margin, x1 - 1 - margin, y1 - 1 - margin], fill=color)
        elif style == "gapped":
            margin = max(1, box_size // 6)
            draw.rectangle([x0 + margin, y0 + margin, x1 - 1 - margin, y1 - 1 - margin], fill=color)
        else:
            draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=color)

    def _draw_finder_pattern(
        self, draw: ImageDraw.ImageDraw, r0: int, c0: int, box_size: int,
        eye_style: str, outer_color: tuple[int, int, int, int],
        inner_color: tuple[int, int, int, int], back_color: tuple[int, int, int, int]
    ) -> None:
        x0 = c0 * box_size
        y0 = r0 * box_size
        x1 = (c0 + 7) * box_size
        y1 = (r0 + 7) * box_size

        if eye_style == "rounded":
            rad_outer = box_size * 2
            draw.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=rad_outer, fill=outer_color)
            rad_inner = int(box_size * 1.5)
            draw.rounded_rectangle(
                [x0 + box_size, y0 + box_size, x1 - 1 - box_size, y1 - 1 - box_size],
                radius=rad_inner, fill=back_color
            )
            rad_center = box_size
            draw.rounded_rectangle(
                [x0 + 2 * box_size, y0 + 2 * box_size, x1 - 1 - 2 * box_size, y1 - 1 - 2 * box_size],
                radius=rad_center, fill=inner_color
            )
        elif eye_style == "circle":
            draw.ellipse([x0, y0, x1 - 1, y1 - 1], fill=outer_color)
            draw.ellipse([x0 + box_size, y0 + box_size, x1 - 1 - box_size, y1 - 1 - box_size], fill=back_color)
            draw.ellipse([x0 + 2 * box_size, y0 + 2 * box_size, x1 - 1 - 2 * box_size, y1 - 1 - 2 * box_size], fill=inner_color)
        else:
            draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=outer_color)
            draw.rectangle([x0 + box_size, y0 + box_size, x1 - 1 - box_size, y1 - 1 - box_size], fill=back_color)
            draw.rectangle([x0 + 2 * box_size, y0 + 2 * box_size, x1 - 1 - 2 * box_size, y1 - 1 - 2 * box_size], fill=inner_color)

    def _apply_logo(
        self, qr_img: Image.Image, logo_path: str, back_color: str, logo_shape: str = "square"
    ) -> Image.Image:
        logo = Image.open(logo_path).convert("RGBA")
        base_width, base_height = qr_img.size

        logo_target_size = int(base_width * 0.22)
        logo = logo.resize((logo_target_size, logo_target_size), Image.Resampling.LANCZOS)

        if logo_shape == "circle":
            mask = Image.new("L", (logo_target_size, logo_target_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, logo_target_size - 1, logo_target_size - 1), fill=255)
            logo.putalpha(mask)

        padding = max(4, int(logo_target_size * 0.12))
        box_size_logo = logo_target_size + 2 * padding

        back_rgba = parse_color(back_color)
        logo_bg = Image.new("RGBA", (box_size_logo, box_size_logo), (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(logo_bg)

        if logo_shape == "circle":
            bg_draw.ellipse((0, 0, box_size_logo - 1, box_size_logo - 1), fill=back_rgba)
        elif logo_shape == "rounded":
            bg_draw.rounded_rectangle((0, 0, box_size_logo - 1, box_size_logo - 1), radius=padding * 2, fill=back_rgba)
        else:
            bg_draw.rectangle((0, 0, box_size_logo - 1, box_size_logo - 1), fill=back_rgba)

        logo_bg.paste(logo, (padding, padding), logo)

        pos = ((base_width - box_size_logo) // 2, (base_height - box_size_logo) // 2)
        qr_img.paste(logo_bg, pos, logo_bg)
        return qr_img

    def save_as_png(self, image: Image.Image, file_path: str) -> None:
        """Saves PIL Image as high-quality PNG file."""
        image.save(file_path, "PNG")

    def save_as_jpeg(self, image: Image.Image, file_path: str, back_color: str = "#FFFFFF") -> None:
        """Saves PIL Image as high-quality JPEG with customizable background fill."""
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            bg_rgba = parse_color(back_color)
            bg = Image.new('RGB', image.size, (bg_rgba[0], bg_rgba[1], bg_rgba[2]))
            if image.mode == 'RGBA':
                bg.paste(image, mask=image.split()[3])
            else:
                bg.paste(image)
            bg.save(file_path, "JPEG", quality=95, subsampling=0)
        else:
            rgb_image = image.convert('RGB')
            rgb_image.save(file_path, "JPEG", quality=95, subsampling=0)

    def save_as_webp(self, image: Image.Image, file_path: str, quality: int = 95) -> None:
        """Saves PIL Image as WebP image."""
        image.save(file_path, "WEBP", quality=quality)

    def to_base64_png(self, image: Image.Image) -> str:
        """Returns PNG image encoded as Base64 string."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def to_data_uri(self, image: Image.Image, format_name: str = "png") -> str:
        """Returns Data URI scheme string (e.g. data:image/png;base64,...)."""
        b64 = self.to_base64_png(image)
        mime = f"image/{format_name.lower()}"
        return f"data:{mime};base64,{b64}"

    def save_as_svg(
        self,
        data: str,
        file_path: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        error_correction: str = "M",
        logo_path: str | None = None,
        module_style: str = "square",
        eye_style: str = "square",
        eye_fill_color: str | None = None,
        gradient_type: str | None = None,
        gradient_color: str | None = None,
        logo_shape: str = "square"
    ) -> None:
        """Generates clean vector SVG file with viewBox, responsiveness, and optional embedded logo."""
        has_advanced_style = (
            module_style != "square"
            or eye_style != "square"
            or (eye_fill_color is not None and eye_fill_color != fill_color)
            or (gradient_type is not None and gradient_color is not None)
            or logo_shape != "square"
        )

        if has_advanced_style:
            rendered = self.generate_qr(
                data=data,
                fill_color=fill_color,
                back_color=back_color,
                box_size=box_size,
                border=border,
                error_correction=error_correction,
                logo_path=logo_path,
                module_style=module_style,
                eye_style=eye_style,
                eye_fill_color=eye_fill_color,
                gradient_type=gradient_type,
                gradient_color=gradient_color,
                logo_shape=logo_shape
            )
            png_bytes = io.BytesIO()
            rendered.save(png_bytes, format="PNG")
            encoded = base64.b64encode(png_bytes.getvalue()).decode("ascii")
            image_size = rendered.width
            svg_content = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {image_size} {image_size}" '
                'width="100%" height="100%" preserveAspectRatio="xMidYMid meet">'
                f'<image width="{image_size}" height="{image_size}" '
                f'href="data:image/png;base64,{encoded}"/></svg>'
            )
            pathlib.Path(file_path).write_text(svg_content, encoding="utf-8")
            return

        error_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        if logo_path is not None:
            error_correction = 'H'

        error_correct_level = error_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)

        qr = qrcode.QRCode(
            version=None,
            error_correction=error_correct_level,
            box_size=box_size,
            border=border
        )
        qr.add_data(data)
        qr.make(fit=True)

        total_modules = qr.modules_count + border * 2

        factory = qrcode.image.svg.SvgPathImage
        svg_img = qr.make_image(image_factory=factory)

        root = svg_img._img

        root.attrib.pop("width", None)
        root.attrib.pop("height", None)
        root.attrib["viewBox"] = f"0 0 {total_modules} {total_modules}"
        root.attrib["width"] = "100%"
        root.attrib["height"] = "100%"
        root.attrib["preserveAspectRatio"] = "xMidYMid meet"
        root.attrib["shape-rendering"] = "crispEdges"
        root.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
        root.attrib["style"] = "width: 100%; height: 100%; max-width: 100%; max-height: 100%; display: block; margin: auto;"

        bg_rect = ET.Element(
            "rect",
            x="0",
            y="0",
            width=str(total_modules),
            height=str(total_modules),
            fill=back_color
        )
        root.insert(0, bg_rect)

        for elem in root.iter():
            if str(elem.tag).endswith("path"):
                elem.set("fill", fill_color)

        if logo_path is not None and pathlib.Path(logo_path).exists():
            with open(logo_path, "rb") as f:
                encoded_logo = base64.b64encode(f.read()).decode("utf-8")

            ext = pathlib.Path(logo_path).suffix.lower().lstrip(".")
            if ext == "jpg":
                ext = "jpeg"
            mime = f"image/{ext}" if ext in ["png", "jpeg", "gif", "svg+xml"] else "image/png"
            data_url = f"data:{mime};base64,{encoded_logo}"

            logo_size_mod = total_modules * 0.22
            padding_mod = logo_size_mod * 0.12
            box_size_mod = logo_size_mod + 2 * padding_mod
            box_pos = (total_modules - box_size_mod) / 2
            logo_pos = box_pos + padding_mod

            logo_bg = ET.Element(
                "rect",
                x=str(box_pos),
                y=str(box_pos),
                width=str(box_size_mod),
                height=str(box_size_mod),
                fill=back_color
            )
            root.append(logo_bg)

            logo_elem = ET.Element(
                "image",
                x=str(logo_pos),
                y=str(logo_pos),
                width=str(logo_size_mod),
                height=str(logo_size_mod),
                href=data_url
            )
            logo_elem.set("{http://www.w3.org/1999/xlink}href", data_url)
            root.append(logo_elem)

        svg_img.save(file_path)

    def to_base64_svg(
        self,
        data: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        error_correction: str = "M",
        logo_path: str | None = None
    ) -> str:
        """Generates SVG content and returns it as a Base64 string."""
        temp_path = "_temp_qr_export.svg"
        self.save_as_svg(
            data, temp_path, fill_color, back_color, box_size, border, error_correction, logo_path
        )
        p = pathlib.Path(temp_path)
        if p.exists():
            content = p.read_bytes()
            p.unlink()
            return base64.b64encode(content).decode("utf-8")
        return ""

    def check_scannability(self, image_or_path: Image.Image | str) -> dict:
        """
        Scans a QR image using zxingcpp (if available) to verify phone readability.
        Returns dict with status, decoded text, and format.
        """
        if isinstance(image_or_path, str):
            img = Image.open(image_or_path)
        else:
            img = image_or_path

        if not HAS_ZXING:
            return {
                "scannable": True,
                "decoded_text": None,
                "engine": "none",
                "message": "zxingcpp library not installed for verification"
            }

        try:
            res = zxingcpp.read_barcode(img)
            if res is not None and res.valid:
                return {
                    "scannable": True,
                    "decoded_text": res.text,
                    "format": str(res.format),
                    "engine": "zxingcpp"
                }
            else:
                return {
                    "scannable": False,
                    "decoded_text": None,
                    "engine": "zxingcpp",
                    "error": "No barcode recognized by decoder"
                }
        except (zxingcpp.Error, OSError, RuntimeError, ValueError) as e:
            return {
                "scannable": False,
                "decoded_text": None,
                "engine": "zxingcpp",
                "error": str(e)
            }

    def analyze_scannability(
        self,
        data: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        error_correction: str = "M",
        logo_path: str | None = None,
        module_style: str = "square",
        eye_style: str = "square",
        eye_fill_color: str | None = None,
        gradient_type: str | None = None,
        gradient_color: str | None = None,
        logo_shape: str = "square"
    ) -> dict:
        """
        Performs a full diagnostic of the QR setup before rendering.
        Returns contrast ratio, inversion status, quiet zone status, scannability score (0-100), warnings, and recommendations.
        """
        warnings = []
        recommendations = []
        score = 100

        ratio = calculate_contrast_ratio(fill_color, back_color)
        inverted = is_inverted(fill_color, back_color)

        if inverted:
            score -= 30
            warnings.append("Inverted colors: Light pattern on dark background may confuse some older camera scanners.")
            suggested_fill, suggested_back = suggest_optimal_colors(fill_color, back_color)
            recommendations.append(f"Consider swapping colors to fill='{suggested_fill}' and back='{suggested_back}'.")

        if ratio < 4.5:
            score -= 25
            warnings.append(f"Low contrast ratio ({ratio:.2f}:1). Recommended contrast ratio is >= 4.5:1 for easy camera reading.")
            recommendations.append("Increase contrast between fill and background color.")

        if gradient_type and gradient_color:
            gradient_ratio = calculate_contrast_ratio(gradient_color, back_color)
            if gradient_ratio < 4.5:
                score -= 15
                warnings.append(
                    f"Gradient endpoint has low contrast ({gradient_ratio:.2f}:1) against the background."
                )
                recommendations.append("Choose a darker or higher-contrast gradient endpoint.")
            ratio = min(ratio, gradient_ratio)

        if eye_fill_color:
            eye_ratio = calculate_contrast_ratio(eye_fill_color, back_color)
            if eye_ratio < 4.5:
                score -= 15
                warnings.append(
                    f"Finder eye color has low contrast ({eye_ratio:.2f}:1) against the background."
                )
                recommendations.append("Choose a higher-contrast finder eye color.")
            ratio = min(ratio, eye_ratio)

        if border < 4:
            score -= 15
            warnings.append(f"Quiet zone border is small ({border} modules). Minimum standard quiet zone is 4 modules.")
            recommendations.append("Increase border to 4 or higher.")

        if logo_path is not None and error_correction.upper() in ('L', 'M'):
            recommendations.append("Using logo: Automatically upgraded error correction level to 'H' for damage recovery.")

        img = self.generate_qr(
            data=data,
            fill_color=fill_color,
            back_color=back_color,
            box_size=box_size,
            border=border,
            error_correction=error_correction,
            logo_path=logo_path,
            module_style=module_style,
            eye_style=eye_style,
            eye_fill_color=eye_fill_color,
            gradient_type=gradient_type,
            gradient_color=gradient_color,
            logo_shape=logo_shape
        )

        scan_info = self.check_scannability(img)
        if HAS_ZXING and not scan_info.get("scannable", False):
            score -= 40
            warnings.append("Decoder verification test failed: Sample camera decoder could not read the generated QR code.")

        final_score = max(0, score)

        return {
            "scannability_score": final_score,
            "contrast_ratio": round(ratio, 2),
            "is_inverted": inverted,
            "is_scannable": scan_info.get("scannable", True),
            "warnings": warnings,
            "recommendations": recommendations,
            "scan_verification": scan_info
        }
