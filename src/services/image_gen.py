from PIL import Image, ImageDraw, ImageFont
import requests
import io
import textwrap
from typing import List, Optional
from functools import lru_cache

class MemeGenerator:
    """
    Класс для наложения текста на изображение-шаблон.
    """
    def __init__(self, font_path: str = "arial.ttf"):
        # Если 'arial.ttf' недоступен, Pillow использует стандартный шрифт
        try:
            self.font_path = font_path
            # For newer Pillow versions, default size might be needed or handled differently, 
            # but initializing with 40 is a start. We resize later.
            self.base_font = ImageFont.truetype(self.font_path, 40)
        except IOError:
            print("Внимание: Стандартный шрифт не найден. Используется дефолтный шрифт PIL.")
            self.font_path = None
            self.base_font = ImageFont.load_default()

    @staticmethod
    @lru_cache(maxsize=128)
    def _download_image_bytes(url: str) -> Optional[bytes]:
        """Скачивает изображение по URL и возвращает байты. Кешируется."""
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при скачивании изображения: {e}")
            return None

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Скачивает изображение по URL и возвращает объект PIL Image."""
        image_bytes = self._download_image_bytes(url)
        if not image_bytes:
            return None
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")

    def _draw_text_with_shadow(self, draw: ImageDraw.Draw, text: str, pos: tuple[int, int], font: ImageFont.ImageFont):
        """Рисует текст с черным контуром/тенью (классический мем-стиль)."""
        x, y = pos
        # Черный контур
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
        # Белый текст
        draw.text((x, y), text, font=font, fill=(255, 255, 255))

    def _wrap_text(self, text: str, max_width: int, font: ImageFont.ImageFont) -> List[str]:
        """Оборачивает текст, чтобы он умещался по ширине изображения."""
        lines = []
        
        # In newer Pillow, getsize is deprecated. Using getbbox or getlength.
        # But for compatibility with the user provided code which used getsize, I will adapt.
        # However, to be safe against deprecation warnings or errors in latest Pillow (>=10.0),
        # I should use getbbox or getlength.
        # Let's try to stick to what works. textwrap works on characters, not pixels.
        
        # Calculate roughly characters that fit.
        # We need a way to measure text width.
        def get_text_width(t, f):
            if hasattr(f, 'getlength'):
                return f.getlength(t)
            return f.getsize(t)[0]

        avg_char_width = get_text_width("A", font)
        max_chars_per_line = int(max_width // avg_char_width) if avg_char_width > 0 else 1
        
        # Используем textwrap для базового переноса
        wrapped_lines = textwrap.wrap(text, width=int(max_chars_per_line * 1.5), break_long_words=False)
        
        # Дополнительная проверка на ширину
        for line in wrapped_lines:
             if get_text_width(line, font) > max_width * 0.95:
                # Если строка все равно слишком длинная, ищем точку разрыва
                temp_line = ""
                words = line.split()
                for word in words:
                    test_line = temp_line + " " + word if temp_line else word
                    if get_text_width(test_line, font) < max_width * 0.95:
                        temp_line = test_line
                    else:
                        lines.append(temp_line)
                        temp_line = word
                if temp_line:
                    lines.append(temp_line)
             else:
                 lines.append(line)
                 
        return lines

    def create_meme(self, image_url: str, top_text: str, bottom_text: str, output_path: str) -> Optional[str]:
        """Основная функция для создания мема."""
        img = self._download_image(image_url)
        if not img:
            return None
        
        # Увеличиваем размер шрифта пропорционально ширине изображения
        width, height = img.size
        font_size = max(int(width / 20), 20)
        
        font = None
        if self.font_path:
             try:
                 font = ImageFont.truetype(self.font_path, font_size)
             except Exception:
                 pass
        
        if font is None:
             font = ImageFont.load_default()
             # Default font size is fixed in old pillow, but in new it can be scalable if it's a truetype font.
             # ImageFont.load_default() returns a bitmap font usually which is not scalable.
             # But let's hope for the best or that arial.ttf exists or we accept small font.
        
        draw = ImageDraw.Draw(img)

        # Helper to get size
        def get_text_size(t, f):
            if hasattr(f, 'getbbox'):
                bbox = f.getbbox(t)
                if bbox:
                    return bbox[2] - bbox[0], bbox[3] - bbox[1]
                return 0, 0
            return f.getsize(t)

        # 1. Верхний текст
        top_lines = self._wrap_text(top_text.upper(), width, font)
        top_y = 0
        for line in top_lines:
            text_width, text_height = get_text_size(line, font)
            x = (width - text_width) / 2
            self._draw_text_with_shadow(draw, line, (int(x), int(top_y)), font)
            top_y += text_height * 1.1 # Смещение для следующей строки

        # 2. Нижний текст
        bottom_lines = self._wrap_text(bottom_text.upper(), width, font)
        # Вычисляем начальную позицию для нижнего текста
        total_bottom_height = sum(get_text_size(line, font)[1] * 1.1 for line in bottom_lines)
        bottom_y = height - total_bottom_height

        for line in bottom_lines:
            text_width, text_height = get_text_size(line, font)
            x = (width - text_width) / 2
            self._draw_text_with_shadow(draw, line, (int(x), int(bottom_y)), font)
            bottom_y += text_height * 1.1

        # Сохраняем результат
        img.save(output_path)
        return output_path
