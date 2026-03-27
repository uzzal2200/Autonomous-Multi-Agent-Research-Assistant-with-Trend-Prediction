"""
ResearchAI - Summarization Agent
Generates paper summaries using free HuggingFace models.
Supports single-paper and multi-document summarization.
"""

import uuid
from typing import Optional

from src.agents.base_agent import BaseAgent
from src.models.data_models import Paper, PaperSummary
from src.utils.text_processing import clean_text, truncate_text
from config.settings import model_settings, app_settings


class SummarizationAgent(BaseAgent):
    """Summarizes academic papers using free HuggingFace models.

    Models:
        - facebook/bart-large-cnn (default, high quality)
        - t5-small (lighter alternative)

    Supports:
        - Single paper summarization
        - Multi-document summarization (map-reduce)
    """

    def __init__(self, **kwargs):
        super().__init__(name="summarization", **kwargs)
        self._summarizer = None

    def _get_summarizer(self):
        """Lazy-load the free summarization pipeline."""
        if self._summarizer is None:
            try:
                from transformers import pipeline
                self._summarizer = pipeline(
                    "summarization",
                    model=model_settings.summarization_model,
                    device=-1,  # CPU
                )
                self.logger.info(f"Summarizer loaded: {model_settings.summarization_model}")
            except Exception as e:
                self.logger.warning(f"Summarizer not available: {e}. Using extractive fallback.")
        return self._summarizer

    # ── Main Entry Point ─────────────────────────────────────────────

    def process(
        self,
        papers: list[Paper],
        mode: str = "single",
    ) -> list[PaperSummary]:
        """Generate summaries for papers.

        Args:
            papers: List of Paper objects.
            mode: "single" for per-paper, "multi" for aggregated summary.

        Returns:
            List of PaperSummary objects.
        """
        if mode == "multi" and len(papers) > 1:
            summary = self._multi_document_summary(papers)
            return [summary]
        else:
            summaries = []
            for paper in papers:
                summary = self._single_paper_summary(paper)
                if summary:
                    summaries.append(summary)
            return summaries

    # ── Single Paper Summary ─────────────────────────────────────────

    def _single_paper_summary(self, paper: Paper) -> Optional[PaperSummary]:
        """Generate a summary for a single paper."""
        text = paper.full_text or paper.abstract
        if not text:
            return None

        cleaned = clean_text(text)
        summary_text = self._generate_summary(cleaned)

        # Extract structured components
        contributions = self._extract_contributions(cleaned)
        methodology = self._extract_section(cleaned, "method")
        results = self._extract_section(cleaned, "result")
        limitations = self._extract_section(cleaned, "limitation")

        return PaperSummary(
            summary_id=f"sum_{uuid.uuid4().hex[:8]}",
            paper_ids=[paper.paper_id],
            summary_text=summary_text,
            key_contributions=contributions,
            methodology=methodology,
            results=results,
            limitations=limitations,
            summary_type="single",
        )

    # ── Multi-Document Summary ───────────────────────────────────────

    def _multi_document_summary(self, papers: list[Paper]) -> PaperSummary:
        """Generate an aggregated summary across multiple papers (map-reduce)."""
        # Map phase: summarize each paper
        individual_summaries = []
        for paper in papers:
            text = paper.full_text or paper.abstract
            if text:
                cleaned = clean_text(text)
                summary = self._generate_summary(cleaned)
                individual_summaries.append(
                    f"[{paper.title}]: {summary}"
                )

        # Reduce phase: summarize the summaries
        combined = "\n\n".join(individual_summaries)
        if len(combined) > 2000:
            combined = truncate_text(combined, 2000)

        meta_summary = self._generate_summary(combined)

        return PaperSummary(
            summary_id=f"sum_{uuid.uuid4().hex[:8]}",
            paper_ids=[p.paper_id for p in papers],
            summary_text=meta_summary,
            key_contributions=[
                f"Synthesis of {len(papers)} papers",
                "Cross-paper comparison and analysis",
            ],
            summary_type="multi",
        )

    # ── Summary Generation ───────────────────────────────────────────

    def _generate_summary(self, text: str) -> str:
        """Generate summary using HuggingFace model or extractive fallback."""
        summarizer = self._get_summarizer()

        if summarizer:
            try:
                # BART/T5 have max input length
                truncated = truncate_text(text, 1024)
                if len(truncated) < 50:
                    return truncated

                result = summarizer(
                    truncated,
                    max_length=app_settings.summary_max_length,
                    min_length=app_settings.summary_min_length,
                    do_sample=False,
                )
                return result[0]["summary_text"]

            except Exception as e:
                self.logger.warning(f"Model summarization failed: {e}")

        # Extractive fallback: take first few sentences
        return self._extractive_summary(text)

    def _extractive_summary(self, text: str, num_sentences: int = 5) -> str:
        """Simple extractive summary — first N sentences."""
        sentences = text.split(". ")
        selected = sentences[:num_sentences]
        return ". ".join(selected) + ("." if selected else "")

    # ── Section Extraction ───────────────────────────────────────────

    def _extract_contributions(self, text: str) -> list[str]:
        """Extract key contributions from text."""
        contribution_keywords = [
            "we propose", "we present", "we introduce", "our contribution",
            "we demonstrate", "we show that", "novel", "first to",
            "main contribution", "key insight",
        ]

        sentences = text.split(". ")
        contributions = []
        for sentence in sentences:
            lower = sentence.lower()
            if any(kw in lower for kw in contribution_keywords):
                clean = sentence.strip()
                if len(clean) > 20:
                    contributions.append(clean[:200])

        return contributions[:5] if contributions else ["See paper abstract for details."]

    def _extract_section(self, text: str, section_type: str) -> str:
        """Extract a specific section's content (methodology, results, etc.)."""
        section_keywords = {
            "method": ["method", "approach", "technique", "algorithm", "framework"],
            "result": ["result", "performance", "accuracy", "evaluation", "experiment"],
            "limitation": ["limitation", "drawback", "future work", "challenge", "restrict"],
        }

        keywords = section_keywords.get(section_type, [])
        sentences = text.split(". ")
        relevant = []

        for sentence in sentences:
            lower = sentence.lower()
            if any(kw in lower for kw in keywords):
                relevant.append(sentence.strip())

        if relevant:
            return ". ".join(relevant[:3]) + "."
        return f"No explicit {section_type} section identified."
