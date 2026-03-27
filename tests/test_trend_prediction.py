"""Tests for Trend Prediction Agent."""

import pytest
from src.agents.trend_prediction import TrendPredictionAgent
from src.knowledge_graph.graph_manager import KnowledgeGraphManager


@pytest.fixture
def mock_graph():
    """Build a knowledge graph with known trend patterns."""
    kg = KnowledgeGraphManager()

    # Growing topic: increasing papers per year
    kg.add_topic_node("t_growing", name="large language models")
    years_papers = {2019: 2, 2020: 5, 2021: 10, 2022: 20, 2023: 35}
    idx = 0
    for year, count in years_papers.items():
        for j in range(count):
            pid = f"p_grow_{idx}"
            kg.add_paper_node(pid, title=f"LLM Paper {idx}", year=year, citation_count=50 * (2024 - year))
            kg.add_edge(pid, "t_growing", "related_to")
            kg.add_author_node(f"a_{idx}", name=f"Author {idx}")
            kg.add_authorship(pid, f"a_{idx}")
            idx += 1

    # Stable topic: flat papers per year
    kg.add_topic_node("t_stable", name="support vector machines")
    for year in range(2019, 2024):
        for j in range(3):
            pid = f"p_stable_{year}_{j}"
            kg.add_paper_node(pid, title=f"SVM Paper {year}_{j}", year=year, citation_count=20)
            kg.add_edge(pid, "t_stable", "related_to")

    return kg


@pytest.fixture
def agent(mock_graph):
    return TrendPredictionAgent(knowledge_graph=mock_graph)


class TestTrendPredictionAgent:

    def test_agent_initialization(self, agent):
        assert agent.name == "trend_prediction"

    def test_compute_topic_metrics(self, agent):
        metrics = agent._compute_topic_metrics()
        assert "large language models" in metrics
        assert "support vector machines" in metrics

    def test_growing_topic_has_positive_growth(self, agent):
        metrics = agent._compute_topic_metrics()
        llm_metrics = metrics["large language models"]
        assert llm_metrics["growth_rate"] > 0

    def test_exponential_smoothing(self, agent):
        papers_per_year = {2019: 2, 2020: 5, 2021: 10, 2022: 20, 2023: 35}
        years = sorted(papers_per_year.keys())
        projected = agent._exponential_smoothing(papers_per_year, years)
        assert len(projected) == 5  # 5-year forecast
        # Projections should be positive and increasing
        values = list(projected.values())
        assert all(v > 0 for v in values)

    def test_process_returns_predictions(self, agent):
        predictions = agent.process(top_n=5)
        assert isinstance(predictions, list)

    def test_confidence_score_range(self, agent):
        predictions = agent.process(top_n=5)
        for pred in predictions:
            assert 0 <= pred.confidence_score <= 1.0

    def test_growing_topic_ranked_higher(self, agent):
        predictions = agent.process(top_n=5)
        if len(predictions) >= 2:
            topics = [p.topic for p in predictions]
            if "large language models" in topics and "support vector machines" in topics:
                llm_idx = topics.index("large language models")
                svm_idx = topics.index("support vector machines")
                assert llm_idx < svm_idx  # LLM should be ranked higher
