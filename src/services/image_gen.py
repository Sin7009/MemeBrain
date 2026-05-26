from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import requests
import io
import textwrap
import logging
from typing import List, Optional
from functools import lru_cache

class MemeGenerator:
    """
    Класс для наложения текста на изображение-шаблон.
    """
    def __init__(self, font_path: str = "arial.ttf"):
        # Если 'arial.ttf' недоступен, Pillow использует стандартный шрифт
        self.font_path = font_path

    @staticmethod
    @lru_cache(maxsize=128)
    def _download_image_bytes(url: str) -> Optional[bytes]:
        """Скачивает изображение по URL и возвращает байты. Кешируется."""
        MAX_SIZE = 5 * 1024 * 1024  # Лимит 5 МБ
        try:
            with requests.get(url, stream=True, timeout=10) as response:
                response.raise_for_status()

                # Проверяем Content-Length, если есть
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > MAX_SIZE:
                    logging.warning("Изображение слишком большое: %s байт", content_length)
                    return None

                # Использование io.BytesIO для эффективного накопления байтов
                buffer = io.BytesIO()
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    buffer.write(chunk)
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_SIZE:
                        logging.warning("Превышен лимит размера изображения")
                        return None
                return buffer.getvalue()
        except requests.exceptions.RequestException as e:
            logging.error("Ошибка при скачивании изображения: %s", e)
            return None
        except ValueError:
            logging.error("Ошибка парсинга Content-Length")
            return None

    @staticmethod
    @lru_cache(maxsize=16)
    def _get_cached_image_object(url: str) -> Optional[Image.Image]:
        """
        Извлекает декодированный объект PIL Image из кэша.
        """
        image_bytes = MemeGenerator._download_image_bytes(url)
        if not image_bytes:
            return None
        try:
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, Exception) as e:
            logging.error("Ошибка при открытии изображения: %s", e)
            return None

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Скачивает изображение по URL и возвращает копию объекта PIL Image."""
        img = self._get_cached_image_object(url)
        if img:
            return img.copy()
        return None

    def _draw_text_with_shadow(self, draw: ImageDraw.Draw, text: str, pos: tuple[int, int], font: ImageFont.ImageFont):
        """Рисует текст с черным контуром/тенью (классический мем-стиль)."""
        x, y = pos
        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

    def _wrap_text(self, text: str, max_width: int, font: ImageFont.ImageFont) -> List[str]:
        """Оборачивает текст, чтобы он умещался по ширине изображения."""
        lines = []
        
        def get_text_width(t, f):
            if hasattr(f, 'getlength'):
                return f.getlength(t)
            return f.getsize(t)[0]

        avg_char_width = get_text_width("A", font)
        max_chars_per_line = int(max_width // avg_char_width) if avg_char_width > 0 else 1
        
        if max_chars_per_line < 1:
            max_chars_per_line = 1

        wrap_width = max(1, int(max_chars_per_line * 1.5))
        wrapped_lines = textwrap.wrap(text, width=wrap_width, break_long_words=False)
        
        for line in wrapped_lines:
            if get_text_width(line, font) > max_width * 0.95:
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

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_font(font_path: Optional[str], size: int) -> ImageFont.ImageFont:
        """Загружает и кэширует объект шрифта."""
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
        
        width, height = img.size

        # Защита от деления на ноль на слишком маленьких картинках
        if width < 10 or height < 10:
            logging.warning("Изображение слишком маленькое: %sx%s", width, height)
            return None

        font_size = max(int(width / 20), 20)
        font = self._get_font(self.font_path, font_size)
        draw = ImageDraw.Draw(img)

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
            top_y += text_height * 1.1

        # 2. Нижний текст
        bottom_lines = self._wrap_text(bottom_text.upper(), width, font)
        total_bottom_height = sum(get_text_size(line, font)[1] * 1.1 for line in bottom_lines)
        bottom_y = height - total_bottom_height

        for line in bottom_lines:
            text_width, text_height = get_text_size(line, font)
            x = (width - text_width) / 2
            self._draw_text_with_shadow(draw, line, (int(x), int(bottom_y)), font)
            bottom_y += text_height * 1.1

        img.save(output_path)
        return output_path
