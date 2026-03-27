"""
ResearchAI - Pydantic Data Models
All core data structures used across agents.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Author(BaseModel):
    """Represents a paper author."""
    name: str
    affiliation: Optional[str] = None
    author_id: Optional[str] = None  # Semantic Scholar / arXiv ID


class Paper(BaseModel):
    """Represents an academic paper with full metadata."""
    paper_id: str
    title: str
    abstract: str = ""
    authors: list[Author] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: int = 0
    references: list[str] = Field(default_factory=list)  # list of paper_ids
    cited_by: list[str] = Field(default_factory=list)
    source: str = ""  # "arxiv", "semantic_scholar", "pubmed"
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    full_text: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=datetime.now)


class KnowledgeEntity(BaseModel):
    """An entity extracted from a paper for the knowledge graph."""
    entity_id: str
    entity_type: str  # "method", "dataset", "topic", "result", "limitation"
    name: str
    description: str = ""
    source_paper_id: str = ""
    confidence: float = 1.0


class KnowledgeRelation(BaseModel):
    """A relationship between two knowledge entities."""
    source_id: str
    target_id: str
    relation_type: str  # "uses", "improves", "contradicts", "extends", "cites"
    weight: float = 1.0
    source_paper_id: str = ""


class ResearchGap(BaseModel):
    """A detected gap in the research landscape."""
    gap_id: str
    topic: str
    description: str
    gap_type: str  # "underexplored", "contradictory", "missing_dataset", "missing_method"
    evidence_papers: list[str] = Field(default_factory=list)  # paper_ids
    novelty_score: float = 0.0  # 0-1, higher = more novel
    priority_rank: int = 0


class ExperimentSuggestion(BaseModel):
    """A suggested experiment based on a detected gap."""
    suggestion_id: str
    gap_id: str
    title: str
    hypothesis: str
    methodology: str
    recommended_datasets: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    expected_outcomes: str = ""
    difficulty: str = "medium"  # "easy", "medium", "hard"


class PaperSummary(BaseModel):
    """A generated summary of one or more papers."""
    summary_id: str
    paper_ids: list[str] = Field(default_factory=list)
    summary_text: str
    key_contributions: list[str] = Field(default_factory=list)
    methodology: str = ""
    results: str = ""
    limitations: str = ""
    summary_type: str = "single"  # "single" or "multi"


class TrendPrediction(BaseModel):
    """A predicted emerging research topic."""
    prediction_id: str
    topic: str
    description: str
    confidence_score: float = 0.0  # 0-1
    time_horizon: str = "5_years"  # "5_years" or "10_years"
    supporting_evidence: list[str] = Field(default_factory=list)
    growth_rate: float = 0.0  # papers/year growth
    citation_velocity: float = 0.0  # citations/year acceleration
    current_paper_count: int = 0
