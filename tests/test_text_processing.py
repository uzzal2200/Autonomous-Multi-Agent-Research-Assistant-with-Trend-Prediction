"""Tests for text processing utilities."""

import pytest
from src.utils.text_processing import (
    clean_text, chunk_text, extract_keywords,
    extract_bigrams, truncate_text,
)


class TestCleanText:
    def test_removes_urls(self):
        result = clean_text("Visit http://example.com for details")
        assert "http" not in result

    def test_removes_emails(self):
        result = clean_text("Contact user@example.com for info")
        assert "@" not in result

    def test_normalizes_whitespace(self):
        result = clean_text("too   many    spaces")
        assert "   " not in result


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunks = chunk_text("Short text.", chunk_size=100)
        assert len(chunks) == 1

    def test_long_text_multiple_chunks(self):
        text = ". ".join(["This is sentence number " + str(i) for i in range(100)])
        chunks = chunk_text(text, chunk_size=200)
        assert len(chunks) > 1

    def test_chunks_not_empty(self):
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text(text, chunk_size=30)
        for chunk in chunks:
            assert len(chunk.strip()) > 0


class TestExtractKeywords:
    def test_extracts_keywords(self):
        text = "Graph neural networks process graph-structured data. Neural networks learn representations."
        keywords = extract_keywords(text, top_n=5)
        assert len(keywords) > 0
        assert any("graph" in kw or "neural" in kw for kw in keywords)

    def test_filters_stopwords(self):
        keywords = extract_keywords("The is a an this that which", top_n=5)
        assert len(keywords) == 0

    def test_respects_top_n(self):
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        keywords = extract_keywords(text, top_n=3)
        assert len(keywords) <= 3


class TestTruncateText:
    def test_short_text_unchanged(self):
        result = truncate_text("Short text.", max_length=100)
        assert result == "Short text."

    def test_truncates_at_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        result = truncate_text(text, max_length=30)
        assert len(result) <= 33  # Some tolerance for "..."
