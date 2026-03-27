"""Tests for Knowledge Graph Manager."""

import pytest
from src.knowledge_graph.graph_manager import KnowledgeGraphManager


@pytest.fixture
def kg():
    """Create a fresh knowledge graph for testing."""
    return KnowledgeGraphManager()


@pytest.fixture
def populated_kg(kg):
    """Create a knowledge graph with sample data."""
    # Add papers
    kg.add_paper_node("p1", title="GNN Survey", year=2022, citation_count=500)
    kg.add_paper_node("p2", title="Transformer Paper", year=2017, citation_count=9000)
    kg.add_paper_node("p3", title="BERT Paper", year=2019, citation_count=7000)

    # Add topics
    kg.add_topic_node("t1", name="graph neural networks")
    kg.add_topic_node("t2", name="transformers")
    kg.add_topic_node("t3", name="NLP")

    # Add methods
    kg.add_method_node("m1", name="attention mechanism")

    # Add authors
    kg.add_author_node("a1", name="John Doe")

    # Add edges
    kg.add_edge("p1", "t1", "related_to")
    kg.add_edge("p2", "t2", "related_to")
    kg.add_edge("p3", "t3", "related_to")
    kg.add_edge("p2", "m1", "uses_method")
    kg.add_citation("p1", "p2", year=2022)
    kg.add_citation("p3", "p2", year=2019)
    kg.add_authorship("p1", "a1")

    return kg


class TestKnowledgeGraphManager:
    """Tests for KnowledgeGraphManager."""

    def test_add_node(self, kg):
        kg.add_node("test_1", "paper", title="Test Paper")
        node = kg.get_node("test_1")
        assert node is not None
        assert node["node_type"] == "paper"
        assert node["title"] == "Test Paper"

    def test_add_paper_node(self, kg):
        kg.add_paper_node("p1", title="Paper 1", year=2023)
        node = kg.get_node("p1")
        assert node["node_type"] == "paper"
        assert node["year"] == 2023

    def test_add_edge(self, kg):
        kg.add_node("n1", "paper")
        kg.add_node("n2", "topic")
        kg.add_edge("n1", "n2", "related_to", weight=0.9)
        neighbors = kg.get_neighbors("n1")
        assert len(neighbors) == 1
        assert neighbors[0]["id"] == "n2"

    def test_get_nodes_by_type(self, populated_kg):
        papers = populated_kg.get_nodes_by_type("paper")
        assert len(papers) == 3
        topics = populated_kg.get_nodes_by_type("topic")
        assert len(topics) == 3

    def test_search_nodes(self, populated_kg):
        results = populated_kg.search_nodes("GNN", node_type="paper")
        assert len(results) == 1
        assert "GNN" in results[0]["title"]

    def test_get_centrality(self, populated_kg):
        centrality = populated_kg.get_centrality(top_n=5)
        assert len(centrality) > 0
        # p2 (Transformer) should have high centrality (most cited)

    def test_find_sparse_regions(self, populated_kg):
        sparse = populated_kg.find_sparse_regions(min_connections=2)
        assert isinstance(sparse, list)

    def test_get_stats(self, populated_kg):
        stats = populated_kg.get_stats()
        assert stats["total_nodes"] == 8  # 3 papers + 3 topics + 1 method + 1 author
        assert stats["total_edges"] > 0
        assert "paper" in stats["node_types"]

    def test_get_citation_network(self, populated_kg):
        citation_graph = populated_kg.get_citation_network()
        assert citation_graph.number_of_edges() == 2  # p1→p2, p3→p2

    def test_save_and_load(self, populated_kg, tmp_path):
        save_path = str(tmp_path / "test_graph.json")
        populated_kg.save(save_path)

        new_kg = KnowledgeGraphManager()
        new_kg.load(save_path)
        assert new_kg.graph.number_of_nodes() == populated_kg.graph.number_of_nodes()

    def test_clear(self, populated_kg):
        populated_kg.clear()
        assert populated_kg.graph.number_of_nodes() == 0
