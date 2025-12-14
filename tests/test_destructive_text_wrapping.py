import pytest
from unittest.mock import MagicMock
from src.services.image_gen import MemeGenerator

class TestDestructiveTextWrapping:
    """
    Test suite specifically for text wrapping edge cases in MemeGenerator.
    """

    def test_wrap_text_crash_on_narrow_width(self):
        """
        Critical Function: _wrap_text in MemeGenerator.
        Failure Point: textwrap.wrap raises ValueError when calculated width is 0.

        Logic Prone to Failure:
        The function calculates `max_chars_per_line = int(max_width // avg_char_width)`.
        If `max_width` < `avg_char_width`, this becomes 0.
        Then `textwrap.wrap` is called with `width=int(0 * 1.5) = 0`, causing a crash.

        This can happen if the image is small (e.g. 10px wide) but the font size constraint
        (min 20px) forces a large character width.
        """
        generator = MemeGenerator()

        # Mock font to simulate a scenario where characters are wider than the image width
        mock_font = MagicMock()
        # Assume max_width will be 10. We return a character width of 12.
        # Support both getlength (newer Pillow) and getsize (older Pillow)
        mock_font.getlength.return_value = 12.0
        mock_font.getsize.return_value = (12, 20)

        max_width = 10
        text = "TEST"

        # This call should handle the edge case gracefully instead of crashing.
        # Prior to fix, this raises ValueError: invalid width 0 (must be > 0)
        try:
            result = generator._wrap_text(text, max_width, mock_font)
            # If successful, result should be a list of strings
            assert isinstance(result, list)
        except ValueError as e:
            pytest.fail(f"Crash detected: {e}")
