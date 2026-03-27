"""
ResearchAI - Knowledge Graph Manager
NetworkX-based knowledge graph for papers, authors, topics, methods, and datasets.
"""

import json
from pathlib import Path
from typing import Optional
from collections import defaultdict

import networkx as nx

from src.utils.logger import get_logger
from config.settings import storage_settings

logger = get_logger("knowledge_graph")


class KnowledgeGraphManager:
    """Manages a knowledge graph of research entities and relationships.

    Node types: paper, author, topic, method, dataset, result
    Edge types: cites, authored_by, uses_method, uses_dataset, related_to, contradicts
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._save_path = storage_settings.graph_save_path

    # ── Node Operations ──────────────────────────────────────────────

    def add_node(
        self,
        node_id: str,
        node_type: str,
        **attributes,
    ) -> None:
        """Add a node to the knowledge graph.

        Args:
            node_id: Unique identifier for the node.
            node_type: Type of node (paper, author, topic, method, dataset).
            **attributes: Additional node attributes (name, description, year, etc.).
        """
        self.graph.add_node(node_id, node_type=node_type, **attributes)
        logger.debug(f"Added {node_type} node: {node_id}")

    def add_paper_node(self, paper_id: str, title: str, year: int = 0, **attrs) -> None:
        self.add_node(paper_id, "paper", title=title, year=year, **attrs)

    def add_author_node(self, author_id: str, name: str, **attrs) -> None:
        self.add_node(author_id, "author", name=name, **attrs)

    def add_topic_node(self, topic_id: str, name: str, **attrs) -> None:
        self.add_node(topic_id, "topic", name=name, **attrs)

    def add_method_node(self, method_id: str, name: str, **attrs) -> None:
        self.add_node(method_id, "method", name=name, **attrs)

    def add_dataset_node(self, dataset_id: str, name: str, **attrs) -> None:
        self.add_node(dataset_id, "dataset", name=name, **attrs)

    # ── Edge Operations ──────────────────────────────────────────────

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        **attributes,
    ) -> None:
        """Add a directed edge between two nodes.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            relation_type: Type of relationship.
            weight: Edge weight.
            **attributes: Additional edge attributes.
        """
        self.graph.add_edge(
            source_id, target_id,
            relation_type=relation_type,
            weight=weight,
            **attributes,
        )

    def add_citation(self, citing_id: str, cited_id: str, year: int = 0) -> None:
        self.add_edge(citing_id, cited_id, "cites", year=year)

    def add_authorship(self, paper_id: str, author_id: str) -> None:
        self.add_edge(paper_id, author_id, "authored_by")

    # ── Query Operations ─────────────────────────────────────────────

    def get_nodes_by_type(self, node_type: str) -> list[dict]:
        """Get all nodes of a specific type."""
        return [
            {"id": n, **self.graph.nodes[n]}
            for n in self.graph.nodes
            if self.graph.nodes[n].get("node_type") == node_type
        ]

    def get_node(self, node_id: str) -> Optional[dict]:
        """Get a single node by ID."""
        if node_id in self.graph:
            return {"id": node_id, **self.graph.nodes[node_id]}
        return None

    def get_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> list[dict]:
        """Get all neighbors of a node, optionally filtered by relation type."""
        neighbors = []
        for _, target, data in self.graph.edges(node_id, data=True):
            if relation_type is None or data.get("relation_type") == relation_type:
                neighbors.append({"id": target, **self.graph.nodes[target], "edge": data})
        return neighbors

    def get_subgraph(self, node_ids: list[str]) -> nx.DiGraph:
        """Extract a subgraph containing the specified nodes."""
        return self.graph.subgraph(node_ids).copy()

    def search_nodes(self, query: str, node_type: Optional[str] = None) -> list[dict]:
        """Search nodes by name/title containing the query string."""
        results = []
        query_lower = query.lower()
        for node_id, data in self.graph.nodes(data=True):
            if node_type and data.get("node_type") != node_type:
                continue
            name = data.get("name", data.get("title", "")).lower()
            if query_lower in name:
                results.append({"id": node_id, **data})
        return results

    # ── Analysis Operations ──────────────────────────────────────────

    def get_centrality(self, top_n: int = 20) -> list[tuple[str, float]]:
        """Compute PageRank centrality for all nodes.

        Returns:
            Sorted list of (node_id, centrality_score) tuples.
        """
        if len(self.graph) == 0:
            return []
        centrality = nx.pagerank(self.graph, weight="weight")
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]

    def detect_communities(self) -> list[set[str]]:
        """Detect communities using greedy modularity on undirected projection."""
        if len(self.graph) == 0:
            return []
        undirected = self.graph.to_undirected()
        try:
            from networkx.algorithms.community import greedy_modularity_communities
            communities = greedy_modularity_communities(undirected, weight="weight")
            return [set(c) for c in communities]
        except Exception as e:
            logger.warning(f"Community detection failed: {e}")
            return []

    def find_sparse_regions(self, min_connections: int = 2) -> list[dict]:
        """Find nodes with very few connections (potential research gaps).

        Args:
            min_connections: Threshold — nodes with fewer connections are 'sparse'.

        Returns:
            List of sparse node dicts.
        """
        sparse = []
        for node_id, degree in self.graph.degree():
            if degree < min_connections:
                data = self.graph.nodes[node_id]
                sparse.append({"id": node_id, "degree": degree, **data})
        return sorted(sparse, key=lambda x: x["degree"])

    def get_topic_coverage(self) -> dict[str, int]:
        """Count papers per topic to identify under/over-explored areas."""
        coverage = defaultdict(int)
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "topic":
                # Count papers connected to this topic
                paper_count = sum(
                    1 for _, _, d in self.graph.in_edges(node_id, data=True)
                    if d.get("relation_type") == "related_to"
                )
                paper_count += sum(
                    1 for _, _, d in self.graph.out_edges(node_id, data=True)
                    if d.get("relation_type") == "related_to"
                )
                coverage[data.get("name", node_id)] = paper_count
        return dict(sorted(coverage.items(), key=lambda x: x[1]))

    def get_citation_network(self) -> nx.DiGraph:
        """Extract the citation-only subgraph (paper → paper edges)."""
        citation_edges = [
            (u, v, d) for u, v, d in self.graph.edges(data=True)
            if d.get("relation_type") == "cites"
        ]
        citation_graph = nx.DiGraph()
        for u, v, d in citation_edges:
            citation_graph.add_node(u, **self.graph.nodes.get(u, {}))
            citation_graph.add_node(v, **self.graph.nodes.get(v, {}))
            citation_graph.add_edge(u, v, **d)
        return citation_graph

    # ── Graph Statistics ─────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get summary statistics about the knowledge graph."""
        node_types = defaultdict(int)
        for _, data in self.graph.nodes(data=True):
            node_types[data.get("node_type", "unknown")] += 1

        edge_types = defaultdict(int)
        for _, _, data in self.graph.edges(data=True):
            edge_types[data.get("relation_type", "unknown")] += 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types),
            "is_connected": nx.is_weakly_connected(self.graph) if len(self.graph) > 0 else False,
        }

    # ── Serialization ────────────────────────────────────────────────

    def save(self, path: Optional[str] = None) -> None:
        """Save the knowledge graph to JSON."""
        save_path = Path(path or self._save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = nx.node_link_data(self.graph)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Knowledge graph saved to {save_path} ({self.graph.number_of_nodes()} nodes)")

    def load(self, path: Optional[str] = None) -> None:
        """Load the knowledge graph from JSON."""
        load_path = Path(path or self._save_path)
        if not load_path.exists():
            logger.warning(f"No graph file found at {load_path}")
            return

        with open(load_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data)
        logger.info(f"Knowledge graph loaded: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self.graph.clear()
        logger.info("Knowledge graph cleared")
