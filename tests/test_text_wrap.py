
import pytest
from PIL import ImageFont
from src.services.image_gen import MemeGenerator

class TestMemeGeneratorTextWrap:
    def setup_method(self):
        self.generator = MemeGenerator()
        self.font = ImageFont.load_default()

    def test_wrap_text_short(self):
        text = "Short text"
        max_width = 1000
        lines = self.generator._wrap_text(text, max_width, self.font)
        assert len(lines) == 1
        assert lines[0] == "Short text"

    def test_wrap_text_long_split(self):
        # Use spaces to allow splitting
        text = "A " * 20
        max_width = 60 # Should split
        lines = self.generator._wrap_text(text, max_width, self.font)
        assert len(lines) > 1

    def test_wrap_text_respects_max_width(self):
        text = "This is a long text that should be wrapped multiple times to fit into the small box provided by the test case."
        max_width = 100
        lines = self.generator._wrap_text(text, max_width, self.font)

        for line in lines:
            # We must use the same measurement method as the implementation to verify
            # But here we just want to ensure it's not egregiously wrong.
            # The implementation ensures width < max_width * 0.95
            width = self.font.getlength(line)
            assert width <= max_width, f"Line '{line}' width {width} exceeds max {max_width}"

    def test_wrap_text_very_long_word(self):
        # A word that is longer than max_width should be on its own line.
        # It will just overflow because we don't do character breaking.
        # But we ensure we don't get an empty line (bug fix).
        long_word = "A" * 50
        max_width = 100

        lines = self.generator._wrap_text(long_word, max_width, self.font)
        # Optimized code should produce 1 line (the word itself), not 2 lines (empty + word).
        assert len(lines) == 1
        assert lines[0] == long_word

    def test_wrap_text_empty(self):
        lines = self.generator._wrap_text("", 100, self.font)
        assert lines == []
