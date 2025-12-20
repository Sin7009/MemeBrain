import pytest
from src.utils import safe_json_parse, escape_html, clean_filename

def test_safe_json_parse_valid():
    json_str = '{"key": "value"}'
    assert safe_json_parse(json_str) == {"key": "value"}

def test_safe_json_parse_with_markdown():
    json_str = '```json\n{"key": "value"}\n```'
    assert safe_json_parse(json_str) == {"key": "value"}

def test_safe_json_parse_invalid():
    json_str = 'invalid json'
    assert safe_json_parse(json_str) is None  # Changed from {} to None

def test_escape_html():
    text = "<b>bold</b> & <script>"
    expected = "&lt;b&gt;bold&lt;/b&gt; &amp; &lt;script&gt;"
    assert escape_html(text) == expected

def test_clean_filename():
    filename = "My/File:Name?.jpg"
    expected = "MyFileName.jpg"
    assert clean_filename(filename) == expected
