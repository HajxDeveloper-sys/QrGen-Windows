import qrcode
import qrcode.image.svg
from PIL import Image
import pathlib

class QRCodeEngine:
    def generate_qr(self, data: str, fill_color: str, back_color: str, box_size: int, border: int, error_correction: str, logo_path: str | None = None) -> Image.Image:
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
        
        img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGB')
        
        if logo_path is not None:
            logo = Image.open(logo_path).convert("RGBA")
            base_width, base_height = img.size
            logo_size = int(base_width * 0.25)
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            pos = ((base_width - logo_size) // 2, (base_height - logo_size) // 2)
            
            logo_mask = logo.split()[3]
            img.paste(logo, pos, logo_mask)
            
        return img

    def save_as_png(self, image: Image.Image, file_path: str) -> None:
        image.save(file_path, "PNG")

    def save_as_jpeg(self, image: Image.Image, file_path: str) -> None:
        rgb_image = image.convert('RGB')
        rgb_image.save(file_path, "JPEG")

    def save_as_svg(self, data: str, file_path: str, fill_color: str, back_color: str, box_size: int, border: int, error_correction: str) -> None:
        error_map = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }
        
        error_correct_level = error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
        
        factory = qrcode.image.svg.SvgPathImage
        
        img = qrcode.make(
            data,
            image_factory=factory,
            error_correction=error_correct_level,
            box_size=box_size,
            border=border
        )
        img.save(file_path)
