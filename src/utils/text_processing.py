"""
ResearchAI - Text Processing Utilities
Chunking, cleaning, and keyword extraction for NLP pipelines.
"""

import re
import string
from collections import Counter
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger("text_processing")

# Common academic stopwords beyond standard English stopwords
ACADEMIC_STOPWORDS = {
    "et", "al", "fig", "figure", "table", "eq", "equation",
    "ref", "section", "chapter", "pp", "vol", "doi", "isbn",
    "http", "https", "www", "arxiv", "preprint",
}

ENGLISH_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "must", "need",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "which", "who", "whom", "what",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "under", "again", "further", "then", "once",
    "and", "but", "or", "nor", "not", "so", "if", "because", "while",
    "about", "each", "all", "both", "few", "more", "most", "other",
    "some", "such", "only", "own", "same", "than", "too", "very",
}


def clean_text(text: str) -> str:
    """Clean raw text by removing artifacts, normalizing whitespace.

    Args:
        text: Raw text to clean.

    Returns:
        Cleaned text string.
    """
    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)
    # Remove email addresses
    text = re.sub(r"\S+@\S+", "", text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r"[^\w\s.,;:!?\-\(\)]", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
    separator: str = ". ",
) -> list[str]:
    """Split text into overlapping chunks for embedding.

    Uses sentence-aware splitting to avoid breaking mid-sentence.

    Args:
        text: Text to chunk.
        chunk_size: Target character count per chunk.
        overlap: Character overlap between consecutive chunks.
        separator: Sentence separator to split on.

    Returns:
        List of text chunks.
    """
    if len(text) <= chunk_size:
        return [text]

    sentences = text.split(separator)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_length = len(sentence) + len(separator)

        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(separator.join(current_chunk))
            # Keep overlap by retaining last few sentences
            overlap_text = separator.join(current_chunk)
            if len(overlap_text) > overlap:
                # Find sentences that fit within overlap
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) > overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s)
                current_chunk = overlap_sentences
                current_length = overlap_len
            else:
                current_chunk = []
                current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(separator.join(current_chunk))

    logger.debug(f"Chunked {len(text)} chars into {len(chunks)} chunks")
    return chunks


def extract_keywords(
    text: str,
    top_n: int = 15,
    min_word_length: int = 3,
) -> list[str]:
    """Extract keywords from text using frequency-based ranking.

    Filters stopwords and short words, returns top N keywords.

    Args:
        text: Input text.
        top_n: Number of top keywords to return.
        min_word_length: Minimum word length to consider.

    Returns:
        List of keywords ranked by frequency.
    """
    # Tokenize and lowercase
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    # Filter stopwords and short words
    all_stopwords = ENGLISH_STOPWORDS | ACADEMIC_STOPWORDS
    filtered = [
        w for w in words
        if w not in all_stopwords and len(w) >= min_word_length
    ]

    # Count and rank
    counter = Counter(filtered)
    keywords = [word for word, _ in counter.most_common(top_n)]
    return keywords


def extract_bigrams(text: str, top_n: int = 10) -> list[str]:
    """Extract meaningful bigrams (two-word phrases) from text.

    Args:
        text: Input text.
        top_n: Number of top bigrams to return.

    Returns:
        List of bigram strings.
    """
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    all_stopwords = ENGLISH_STOPWORDS | ACADEMIC_STOPWORDS

    bigrams = []
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if (w1 not in all_stopwords and w2 not in all_stopwords
                and len(w1) >= 3 and len(w2) >= 3):
            bigrams.append(f"{w1} {w2}")

    counter = Counter(bigrams)
    return [bg for bg, _ in counter.most_common(top_n)]


def truncate_text(text: str, max_length: int = 1024) -> str:
    """Truncate text to max_length at a sentence boundary.

    Args:
        text: Text to truncate.
        max_length: Maximum character length.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_period = truncated.rfind(".")
    if last_period > max_length // 2:
        return truncated[:last_period + 1]
    return truncated + "..."
