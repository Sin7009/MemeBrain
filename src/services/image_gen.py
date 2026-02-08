from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
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
        self.font_path = font_path
        # ⚡ Optimization: Removed self.base_font as it was unused and re-initialized every time in create_meme

    @staticmethod
    @lru_cache(maxsize=128)
    def _download_image_bytes(url: str) -> Optional[bytes]:
        """Скачивает изображение по URL и возвращает байты. Кешируется."""
        MAX_SIZE = 5 * 1024 * 1024  # 5 MB limit
        try:
            with requests.get(url, stream=True, timeout=10) as response:
                response.raise_for_status()

                # Check Content-Length if present
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > MAX_SIZE:
                    print(f"Изображение слишком большое: {content_length} байт")
                    return None

                # ⚡ Optimized: Use io.BytesIO for O(N) accumulation instead of O(N^2) string/bytes concatenation
                buffer = io.BytesIO()
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    buffer.write(chunk)
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_SIZE:
                        print("Превышен лимит размера изображения")
                        return None
                return buffer.getvalue()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при скачивании изображения: {e}")
            return None
        except ValueError:
             print("Ошибка парсинга Content-Length")
             return None

    @staticmethod
    @lru_cache(maxsize=16)
    def _get_cached_image_object(url: str) -> Optional[Image.Image]:
        """
        Retrieves a decoded PIL Image object from cache.
        Using a smaller cache size (16) because decoded images consume significant memory.
        """
        image_bytes = MemeGenerator._download_image_bytes(url)
        if not image_bytes:
            return None
        try:
            # ⚡ Optimized: Return the object directly to the cache.
            # Callers MUST use .copy() if they intend to modify it.
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, Exception) as e:
            print(f"Ошибка при открытии изображения: {e}")
            return None

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Скачивает изображение по URL и возвращает объект PIL Image."""
        # ⚡ Optimized: Use cached decoded image and return a copy to avoid repeated decoding overhead.
        img = self._get_cached_image_object(url)
        if img:
            return img.copy()
        return None

    def _draw_text_with_shadow(self, draw: ImageDraw.Draw, text: str, pos: tuple[int, int], font: ImageFont.ImageFont):
        """Рисует текст с черным контуром/тенью (классический мем-стиль)."""
        x, y = pos
        # Using built-in stroke which is faster (C-implementation) than drawing 5 times in Python
        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

    @staticmethod
    def _get_text_width(text: str, font: ImageFont.ImageFont) -> float:
        """
        Returns the width of the text using modern Pillow API.
        ⚡ Performance: Avoiding `hasattr` checks and using `getlength` directly saves ~20% overhead in tight loops.
        """
        return font.getlength(text)

    @staticmethod
    def _get_text_size(text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
        """
        Returns (width, height) of the text using modern Pillow API.
        ⚡ Performance: Use `getbbox` (native C) instead of deprecated `getsize` or manual calculation.
        """
        bbox = font.getbbox(text)
        if bbox:
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        return 0, 0

    @staticmethod
    def _wrap_text(text: str, max_width: int, font: ImageFont.ImageFont) -> List[str]:
        """Оборачивает текст, чтобы он умещался по ширине изображения."""
        lines = []
        
        # Calculate roughly characters that fit.
        avg_char_width = MemeGenerator._get_text_width("A", font)
        max_chars_per_line = int(max_width // avg_char_width) if avg_char_width > 0 else 1
        
        # Ensure max_chars_per_line is at least 1 to avoid textwrap.wrap(width=0) error
        # This can happen if the image is very small (e.g. < character width)
        if max_chars_per_line < 1:
            max_chars_per_line = 1

        # Используем textwrap для базового переноса
        # We ensure width is at least 1, even if max_chars_per_line * 1.5 casts to 0 (unlikely if max_chars_per_line >= 1)
        wrap_width = max(1, int(max_chars_per_line * 1.5))
        wrapped_lines = textwrap.wrap(text, width=wrap_width, break_long_words=False)
        
        # Дополнительная проверка на ширину
        for line in wrapped_lines:
             if MemeGenerator._get_text_width(line, font) > max_width * 0.95:
                # Если строка все равно слишком длинная, ищем точку разрыва
                temp_line = ""
                words = line.split()
                for word in words:
                    test_line = temp_line + " " + word if temp_line else word
                    if MemeGenerator._get_text_width(test_line, font) < max_width * 0.95:
                        temp_line = test_line
                    else:
                        lines.append(temp_line)
                        temp_line = word
                if temp_line:
                    lines.append(temp_line)
             else:
                 lines.append(line)
                 
        return lines

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_font(font_path: Optional[str], size: int) -> ImageFont.ImageFont:
        """Loads and caches the font object to avoid disk I/O and parsing overhead."""
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    def create_meme(self, image_url: str, top_text: str, bottom_text: str, output_path: str) -> Optional[str]:
        """Основная функция для создания мема."""
        img = self._download_image(image_url)
        if not img:
            return None
        
        # Увеличиваем размер шрифта пропорционально ширине изображения
        width, height = img.size

        # 🛡️ Sentinel: Prevent division by zero on tiny images
        if width < 10 or height < 10:
            print(f"Image too small: {width}x{height}")
            return None

        font_size = max(int(width / 20), 20)
        
        # ⚡ Optimized: Use cached font loader
        font = self._get_font(self.font_path, font_size)
        
        draw = ImageDraw.Draw(img)

        # 1. Верхний текст
        top_lines = self._wrap_text(top_text.upper(), width, font)
        top_y = 0
        for line in top_lines:
            text_width, text_height = MemeGenerator._get_text_size(line, font)
            x = (width - text_width) / 2
            self._draw_text_with_shadow(draw, line, (int(x), int(top_y)), font)
            top_y += text_height * 1.1 # Смещение для следующей строки

        # 2. Нижний текст
        bottom_lines = self._wrap_text(bottom_text.upper(), width, font)
        # Вычисляем начальную позицию для нижнего текста
        total_bottom_height = sum(MemeGenerator._get_text_size(line, font)[1] * 1.1 for line in bottom_lines)
        bottom_y = height - total_bottom_height

        for line in bottom_lines:
            text_width, text_height = MemeGenerator._get_text_size(line, font)
            x = (width - text_width) / 2
            self._draw_text_with_shadow(draw, line, (int(x), int(bottom_y)), font)
            bottom_y += text_height * 1.1

        # Сохраняем результат
        img.save(output_path)
        return output_path
