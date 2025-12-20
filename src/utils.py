import json
import re
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
        print(f"Ошибка парсинга JSON: {e}")
        print(f"Неудавшийся текст: {text[:200]}...")
        return None

def escape_html(text: str) -> str:
    """Escapes HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def clean_filename(filename: str) -> str:
    """Removes invalid characters from filename."""
    return re.sub(r'[\\/*?:"<>|]', '', filename)
