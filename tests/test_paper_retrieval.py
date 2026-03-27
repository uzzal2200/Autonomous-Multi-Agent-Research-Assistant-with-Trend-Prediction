"""Tests for Paper Retrieval Agent."""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.agents.paper_retrieval import PaperRetrievalAgent
from src.models.data_models import Paper


@pytest.fixture
def agent():
    return PaperRetrievalAgent()


@pytest.fixture
def sample_papers():
    """Load sample papers from data file."""
    data_path = Path(__file__).parent.parent / "data" / "sample_papers.json"
    if data_path.exists():
        with open(data_path, "r") as f:
            return json.load(f)
    return []


class TestPaperRetrievalAgent:
    """Tests for PaperRetrievalAgent."""

    def test_agent_initialization(self, agent):
        assert agent.name == "paper_retrieval"
        assert agent._cache_dir.exists()

    def test_deduplication(self, agent):
        papers = [
            Paper(paper_id="1", title="Test Paper"),
            Paper(paper_id="2", title="Test Paper"),  # Duplicate
            Paper(paper_id="3", title="Another Paper"),
        ]
        unique = agent._deduplicate(papers)
        assert len(unique) == 2

    def test_apply_filters_year(self, agent):
        papers = [
            Paper(paper_id="1", title="Old Paper", year=2015),
            Paper(paper_id="2", title="New Paper", year=2023),
            Paper(paper_id="3", title="Mid Paper", year=2020),
        ]
        filtered = agent._apply_filters(papers, year_from=2019)
        assert len(filtered) == 2

    def test_apply_filters_citations(self, agent):
        papers = [
            Paper(paper_id="1", title="Popular", citation_count=1000),
            Paper(paper_id="2", title="Unpopular", citation_count=5),
        ]
        filtered = agent._apply_filters(papers, min_citations=100)
        assert len(filtered) == 1
        assert filtered[0].paper_id == "1"

    def test_cache_key_deterministic(self, agent):
        key1 = agent._cache_key("arxiv", "GNN", 20)
        key2 = agent._cache_key("arxiv", "GNN", 20)
        assert key1 == key2

    def test_cache_key_different_for_different_inputs(self, agent):
        key1 = agent._cache_key("arxiv", "GNN", 20)
        key2 = agent._cache_key("arxiv", "transformer", 20)
        assert key1 != key2

    def test_run_returns_dict(self, agent):
        """Test that run() returns proper result dict even on failure."""
        with patch.object(agent, "process", side_effect=Exception("test error")):
            result = agent.run(query="test")
            assert result["status"] == "error"
            assert "test error" in result["error"]
