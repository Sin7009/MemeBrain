import json
import logging
from typing import Optional, Dict

def safe_json_parse(text: str) -> Optional[Dict]:
    """
    Пытается безопасно извлечь и распарсить JSON из строки,
    которая может содержать лишний текст или разметку Markdown.
    """
    try:
        # Убираем возможные тройные кавычки Markdown
        text = text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except json.JSONDecodeError as e:
        logging.error("Ошибка парсинга JSON: %s", e)
        logging.error("Неудавшийся текст: %s...", text[:200])
        return None

def escape_html(text: str) -> str:
    """Экранирует специальные символы HTML."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
