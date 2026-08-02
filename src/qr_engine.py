import qrcode
import qrcode.image.svg
from PIL import Image
import pathlib
import xml.etree.ElementTree as ET
import base64


def get_relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return 0.5
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
    except ValueError:
        return 0.5

    def srgb_to_lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)


def calculate_contrast_ratio(fill_color: str, back_color: str) -> float:
    l1 = get_relative_luminance(fill_color)
    l2 = get_relative_luminance(back_color)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_inverted(fill_color: str, back_color: str) -> bool:
    return get_relative_luminance(fill_color) > get_relative_luminance(back_color)


class QRCodeEngine:
    def generate_qr(
        self,
        data: str,
        fill_color: str,
        back_color: str,
        box_size: int,
        border: int,
        error_correction: str,
        logo_path: str | None = None
    ) -> Image.Image:
        error_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        if logo_path is not None:
            error_correction = 'H'

        error_correct_level = error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M)

        qr = qrcode.QRCode(
            version=None,
            error_correction=error_correct_level,
            box_size=box_size,
            border=border
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

        if logo_path is not None and pathlib.Path(logo_path).exists():
            logo = Image.open(logo_path).convert("RGBA")
            base_width, base_height = img.size

            logo_target_size = int(base_width * 0.22)
            logo = logo.resize((logo_target_size, logo_target_size), Image.Resampling.LANCZOS)

            padding = max(4, int(logo_target_size * 0.12))
            box_size_logo = logo_target_size + 2 * padding

            logo_bg = Image.new("RGBA", (box_size_logo, box_size_logo), back_color)
            logo_bg.paste(logo, (padding, padding), logo)

            pos = ((base_width - box_size_logo) // 2, (base_height - box_size_logo) // 2)
            img.paste(logo_bg, pos)

        return img.convert('RGB')

    def save_as_png(self, image: Image.Image, file_path: str) -> None:
        image.save(file_path, "PNG")

    def save_as_jpeg(self, image: Image.Image, file_path: str, back_color: str = "#FFFFFF") -> None:
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            bg = Image.new('RGB', image.size, back_color)
            bg.paste(image, mask=image.split()[3])
            bg.save(file_path, "JPEG", quality=95, subsampling=0)
        else:
            rgb_image = image.convert('RGB')
            rgb_image.save(file_path, "JPEG", quality=95, subsampling=0)

    def save_as_svg(
        self,
        data: str,
        file_path: str,
        fill_color: str,
        back_color: str,
        box_size: int,
        border: int,
        error_correction: str,
        logo_path: str | None = None
    ) -> None:
        error_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        if logo_path is not None:
            error_correction = 'H'

        error_correct_level = error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M)

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



