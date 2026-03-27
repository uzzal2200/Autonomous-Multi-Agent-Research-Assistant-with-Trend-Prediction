"""
ResearchAI - PDF and HTML Parser
Extract text from academic paper files using free tools.
"""

import re
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger("pdf_parser")


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract text content from a PDF file using PyPDF2.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text or None if extraction fails.
    """
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} chars from PDF: {Path(pdf_path).name}")
        return full_text if full_text.strip() else None

    except Exception as e:
        logger.error(f"PDF extraction failed for {pdf_path}: {e}")
        return None


def extract_text_from_html(html_content: str) -> Optional[str]:
    """Extract text from HTML content using BeautifulSoup.

    Args:
        html_content: Raw HTML string.

    Returns:
        Cleaned text content.
    """
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        logger.info(f"Extracted {len(text)} chars from HTML")
        return text if text.strip() else None

    except Exception as e:
        logger.error(f"HTML extraction failed: {e}")
        return None


def extract_sections(text: str) -> dict[str, str]:
    """Attempt to extract common academic paper sections from raw text.

    Looks for sections like Abstract, Introduction, Methods, Results,
    Discussion, Conclusion, References.

    Args:
        text: Full paper text.

    Returns:
        Dictionary mapping section names to their content.
    """
    section_patterns = [
        "abstract", "introduction", "related work", "background",
        "methodology", "methods", "method", "approach",
        "experiments", "experimental setup", "results",
        "discussion", "analysis",
        "conclusion", "conclusions", "future work",
        "references", "bibliography",
    ]

    sections = {}
    pattern = re.compile(
        r"(?:^|\n)\s*(?:\d+\.?\s*)?(" + "|".join(section_patterns) + r")\s*\n",
        re.IGNORECASE | re.MULTILINE,
    )

    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        section_name = match.group(1).strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections[section_name] = content

    if not sections:
        sections["full_text"] = text

    return sections
