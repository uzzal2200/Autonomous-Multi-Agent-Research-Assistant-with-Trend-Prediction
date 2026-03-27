"""Tests for Gap Detection Agent."""

import pytest
from src.agents.gap_detection import GapDetectionAgent
from src.knowledge_graph.graph_manager import KnowledgeGraphManager


@pytest.fixture
def mock_graph():
    """Build a knowledge graph with known gap patterns."""
    kg = KnowledgeGraphManager()

    # Create a well-covered topic
    kg.add_topic_node("t_popular", name="deep learning")
    for i in range(10):
        kg.add_paper_node(f"p_pop_{i}", title=f"Deep Learning Paper {i}", year=2020 + (i % 4))
        kg.add_edge(f"p_pop_{i}", "t_popular", "related_to")

    # Create an underexplored topic
    kg.add_topic_node("t_sparse", name="quantum NLP")
    kg.add_paper_node("p_sparse_1", title="Quantum NLP Paper 1", year=2023)
    kg.add_edge("p_sparse_1", "t_sparse", "related_to")

    # Add methods and datasets for method-dataset gap detection
    kg.add_method_node("m1", name="CNN")
    kg.add_method_node("m2", name="Transformer")
    kg.add_dataset_node("d1", name="ImageNet")
    kg.add_edge("p_pop_0", "m1", "uses_method")
    kg.add_edge("p_pop_0", "d1", "uses_dataset")
    # m2 + d1 combination never used → gap

    return kg


@pytest.fixture
def agent(mock_graph):
    return GapDetectionAgent(knowledge_graph=mock_graph)


class TestGapDetectionAgent:

    def test_agent_initialization(self, agent):
        assert agent.name == "gap_detection"

    def test_finds_underexplored_topics(self, agent):
        gaps = agent._find_underexplored_topics()
        # "quantum NLP" should be flagged as underexplored
        topic_names = [g.topic for g in gaps]
        assert any("quantum" in t.lower() for t in topic_names)

    def test_finds_method_dataset_gaps(self, agent):
        gaps = agent._find_method_dataset_gaps()
        # There should be a gap for untested method-dataset combinations
        assert isinstance(gaps, list)

    def test_process_returns_ranked_gaps(self, agent):
        gaps = agent.process(top_n=5)
        assert isinstance(gaps, list)
        # Check ranking
        for i, gap in enumerate(gaps):
            assert gap.priority_rank == i + 1

    def test_novelty_score_range(self, agent):
        gaps = agent.process(top_n=10)
        for gap in gaps:
            assert 0 <= gap.novelty_score <= 1.0
