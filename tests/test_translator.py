"""Tests for Dutch translation module."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.errors import TranslationError
from src.sources.base import ExtractedContent
from src.translator import (
    _chunk_text,
    _extract_code_blocks,
    _restore_code_blocks,
    translate_text,
    translate_text_preserving_code,
)


class TestCodeBlockExtraction:
    """Tests for code block extraction and restoration."""

    def test_extract_fenced_code_block(self):
        """Test extraction of fenced code blocks."""
        text = "Before ```python\nprint('hello')\n``` after"
        result, blocks = _extract_code_blocks(text)

        assert "___CODE_BLOCK_0___" in result
        assert len(blocks) == 1
        assert "```python" in blocks[0][1]

    def test_extract_inline_code(self):
        """Test extraction of inline code."""
        text = "Use the `print()` function"
        result, blocks = _extract_code_blocks(text)

        assert "___CODE_BLOCK_0___" in result
        assert len(blocks) == 1
        assert "`print()`" in blocks[0][1]

    def test_extract_multiple_code_blocks(self):
        """Test extraction of multiple code blocks."""
        text = "First `code1` then `code2`"
        result, blocks = _extract_code_blocks(text)

        assert len(blocks) == 2
        assert "___CODE_BLOCK_0___" in result
        assert "___CODE_BLOCK_1___" in result

    def test_restore_code_blocks(self):
        """Test restoration of code blocks."""
        text = "Before ___CODE_BLOCK_0___ after"
        blocks = [("___CODE_BLOCK_0___", "`code`")]

        result = _restore_code_blocks(text, blocks)
        assert result == "Before `code` after"

    def test_no_code_blocks(self):
        """Test text with no code blocks."""
        text = "Just regular text"
        result, blocks = _extract_code_blocks(text)

        assert result == text
        assert len(blocks) == 0


class TestTextChunking:
    """Tests for text chunking."""

    def test_short_text_no_chunking(self):
        """Test short text is not chunked."""
        text = "Short text"
        chunks = _chunk_text(text, max_length=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_chunked_by_sentences(self):
        """Test long text is chunked by sentences."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = _chunk_text(text, max_length=30)

        assert len(chunks) >= 2
        # Chunks should not exceed max length
        for chunk in chunks:
            assert len(chunk) <= 30

    def test_very_long_sentence_chunked_by_words(self):
        """Test very long sentence is chunked by words."""
        text = "word " * 20  # 100 chars
        chunks = _chunk_text(text.strip(), max_length=30)

        assert len(chunks) >= 3


class TestTranslateText:
    """Tests for translate_text function."""

    def test_translate_empty_text(self):
        """Test translation of empty text returns empty."""
        result = translate_text("", "en", "nl")
        assert result == ""

    def test_translate_whitespace_only(self):
        """Test translation of whitespace returns whitespace."""
        result = translate_text("   ", "en", "nl")
        assert result == "   "

    @patch("src.translator.GoogleTranslator")
    def test_translate_basic_text(self, mock_translator_class):
        """Test basic text translation."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "Hallo wereld"
        mock_translator_class.return_value = mock_instance

        result = translate_text("Hello world", "en", "nl")

        assert result == "Hallo wereld"
        mock_translator_class.assert_called_once_with(source="en", target="nl")
        mock_instance.translate.assert_called_once_with("Hello world")

    @patch("src.translator.GoogleTranslator")
    def test_translate_handles_error(self, mock_translator_class):
        """Test translation error handling."""
        mock_instance = MagicMock()
        mock_instance.translate.side_effect = Exception("API error")
        mock_translator_class.return_value = mock_instance

        with pytest.raises(TranslationError):
            translate_text("Hello", "en", "nl")


class TestTranslateTextPreservingCode:
    """Tests for translate_text_preserving_code function."""

    def test_preserve_empty_text(self):
        """Test empty text is preserved."""
        result = translate_text_preserving_code("", "en", "nl")
        assert result == ""

    @patch("src.translator.translate_text")
    def test_preserve_inline_code(self, mock_translate):
        """Test inline code is preserved during translation."""
        mock_translate.return_value = "Gebruik de functie"

        result = translate_text_preserving_code(
            "Use the `print()` function", "en", "nl"
        )

        # The translate_text should be called without the code
        call_args = mock_translate.call_args[0][0]
        assert "`print()`" not in call_args

    @patch("src.translator.translate_text")
    def test_preserve_fenced_code_block(self, mock_translate):
        """Test fenced code blocks are preserved."""
        # Mock returns text with placeholder intact (simulating translation)
        def side_effect(text, source, target):
            # Return translated text but keep placeholder
            return text.replace("Example:", "Voorbeeld:")

        mock_translate.side_effect = side_effect

        text = """Example:
```python
print("hello")
```"""
        result = translate_text_preserving_code(text, "en", "nl")

        # Code block should be in result (restored from placeholder)
        assert "```python" in result
        assert 'print("hello")' in result

    def test_all_code_returns_original(self):
        """Test text that is all code returns original."""
        text = "`only_code`"
        result = translate_text_preserving_code(text, "en", "nl")
        assert result == text


class TestExtractedContentTranslation:
    """Tests for ExtractedContent metadata after translation."""

    def test_content_metadata_language(self):
        """Test content can have language metadata."""
        content = ExtractedContent(
            title="Test",
            sections=[],
            images=[],
            metadata={"language": "nl"},
        )

        assert content.metadata.get("language") == "nl"

    def test_content_metadata_original_language(self):
        """Test content can have original language metadata."""
        content = ExtractedContent(
            title="Test",
            sections=[],
            images=[],
            metadata={"language": "nl", "original_language": "en"},
        )

        assert content.metadata.get("original_language") == "en"
