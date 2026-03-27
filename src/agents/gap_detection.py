"""
ResearchAI - Gap Detection Agent
Analyzes the knowledge graph to find research gaps.
"""

import uuid
from collections import defaultdict

from src.agents.base_agent import BaseAgent
from src.models.data_models import ResearchGap


class GapDetectionAgent(BaseAgent):
    """Detects research gaps by analyzing the knowledge graph topology.

    Strategies:
        1. Sparse regions → underexplored topics
        2. Low-coverage topics → missing research
        3. Isolated methods/datasets → untried combinations
        4. High-centrality topics with few recent papers → stagnating areas
    """

    def __init__(self, **kwargs):
        super().__init__(name="gap_detection", **kwargs)

    def process(self, top_n: int = 10) -> list[ResearchGap]:
        """Detect and rank research gaps from the knowledge graph.

        Args:
            top_n: Maximum number of gaps to return.

        Returns:
            Ranked list of ResearchGap objects.
        """
        gaps = []

        # Strategy 1: Find underexplored topics (sparse regions)
        gaps.extend(self._find_underexplored_topics())

        # Strategy 2: Find method-dataset gaps (untried combinations)
        gaps.extend(self._find_method_dataset_gaps())

        # Strategy 3: Find topics with declining activity
        gaps.extend(self._find_stagnating_topics())

        # Strategy 4: Find isolated paper clusters
        gaps.extend(self._find_isolated_clusters())

        # Rank all gaps by novelty score
        gaps.sort(key=lambda g: g.novelty_score, reverse=True)

        # Assign priority ranks
        for i, gap in enumerate(gaps):
            gap.priority_rank = i + 1

        self.logger.info(f"Detected {len(gaps)} research gaps, returning top {top_n}")
        return gaps[:top_n]

    # ── Strategy 1: Underexplored Topics ─────────────────────────────

    def _find_underexplored_topics(self) -> list[ResearchGap]:
        """Find topics with very few connected papers."""
        gaps = []
        coverage = self.kg.get_topic_coverage()

        if not coverage:
            return gaps

        avg_coverage = sum(coverage.values()) / max(len(coverage), 1)

        for topic_name, paper_count in coverage.items():
            if paper_count < max(2, avg_coverage * 0.3):
                # Find evidence papers connected to this topic
                topic_nodes = self.kg.search_nodes(topic_name, node_type="topic")
                evidence = []
                for node in topic_nodes:
                    neighbors = self.kg.get_neighbors(node["id"])
                    evidence.extend([
                        n["id"] for n in neighbors
                        if n.get("node_type") == "paper"
                    ])

                gap = ResearchGap(
                    gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                    topic=topic_name,
                    description=f"'{topic_name}' has only {paper_count} connected papers "
                                f"(average is {avg_coverage:.1f}). This area may be underexplored.",
                    gap_type="underexplored",
                    evidence_papers=evidence[:5],
                    novelty_score=min(1.0, 1.0 - (paper_count / max(avg_coverage, 1))),
                )
                gaps.append(gap)

        return gaps

    # ── Strategy 2: Method-Dataset Gaps ──────────────────────────────

    def _find_method_dataset_gaps(self) -> list[ResearchGap]:
        """Find methods that haven't been tested on popular datasets and vice versa."""
        gaps = []

        methods = self.kg.get_nodes_by_type("method")
        datasets = self.kg.get_nodes_by_type("dataset")

        if not methods or not datasets:
            return gaps

        # Build method→dataset connections via papers
        method_datasets = defaultdict(set)
        dataset_methods = defaultdict(set)

        for method in methods:
            method_id = method["id"]
            # Find papers using this method
            for node_id, _, data in self.kg.graph.in_edges(method_id, data=True):
                if data.get("relation_type") == "uses_method":
                    # Find datasets used by this paper
                    paper_neighbors = self.kg.get_neighbors(node_id, "uses_dataset")
                    for ds in paper_neighbors:
                        method_datasets[method["name"]].add(ds.get("name", ds["id"]))
                        dataset_methods[ds.get("name", ds["id"])].add(method["name"])

        # Popular datasets not tested with most methods
        for dataset in datasets:
            ds_name = dataset.get("name", dataset["id"])
            used_methods = dataset_methods.get(ds_name, set())
            all_method_names = {m.get("name", m["id"]) for m in methods}
            unused_methods = all_method_names - used_methods

            if unused_methods and len(unused_methods) > len(all_method_names) * 0.5:
                gap = ResearchGap(
                    gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                    topic=f"{ds_name} + untested methods",
                    description=f"Dataset '{ds_name}' has not been evaluated with methods: "
                                f"{', '.join(list(unused_methods)[:5])}.",
                    gap_type="missing_method",
                    novelty_score=min(1.0, len(unused_methods) / max(len(all_method_names), 1)),
                )
                gaps.append(gap)

        return gaps

    # ── Strategy 3: Stagnating Topics ────────────────────────────────

    def _find_stagnating_topics(self) -> list[ResearchGap]:
        """Find once-popular topics with declining recent activity."""
        gaps = []
        papers = self.kg.get_nodes_by_type("paper")

        if not papers:
            return gaps

        # Group papers by topic and year
        topic_years = defaultdict(list)
        for paper in papers:
            year = paper.get("year", 0)
            if not year:
                continue
            neighbors = self.kg.get_neighbors(paper["id"], "related_to")
            for neighbor in neighbors:
                if neighbor.get("node_type") == "topic":
                    topic_name = neighbor.get("name", neighbor["id"])
                    topic_years[topic_name].append(year)

        # Detect decline: topics with papers mostly before the median year
        all_years = [y for years in topic_years.values() for y in years]
        if not all_years:
            return gaps

        median_year = sorted(all_years)[len(all_years) // 2]

        for topic, years in topic_years.items():
            total = len(years)
            recent = sum(1 for y in years if y >= median_year)

            if total >= 3 and recent / total < 0.3:
                gap = ResearchGap(
                    gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                    topic=topic,
                    description=f"'{topic}' had {total} papers but only {recent} are recent "
                                f"(after {median_year}). This area may be stagnating and could "
                                f"benefit from new research.",
                    gap_type="underexplored",
                    novelty_score=0.6 + (0.4 * (1 - recent / total)),
                )
                gaps.append(gap)

        return gaps

    # ── Strategy 4: Isolated Clusters ────────────────────────────────

    def _find_isolated_clusters(self) -> list[ResearchGap]:
        """Find disconnected paper clusters that might benefit from bridging research."""
        gaps = []
        communities = self.kg.detect_communities()

        if len(communities) <= 1:
            return gaps

        # Find small, isolated communities
        avg_size = sum(len(c) for c in communities) / len(communities)

        for community in communities:
            if len(community) < max(3, avg_size * 0.3):
                # Get topic names in this cluster
                topics = []
                for node_id in community:
                    node = self.kg.get_node(node_id)
                    if node and node.get("node_type") == "topic":
                        topics.append(node.get("name", node_id))

                if topics:
                    gap = ResearchGap(
                        gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                        topic=", ".join(topics[:3]),
                        description=f"Isolated research cluster with {len(community)} entities "
                                    f"covering topics: {', '.join(topics[:5])}. "
                                    f"Bridging this cluster with mainstream research could yield "
                                    f"novel insights.",
                        gap_type="underexplored",
                        novelty_score=0.7,
                        evidence_papers=[
                            nid for nid in community
                            if self.kg.get_node(nid) and self.kg.get_node(nid).get("node_type") == "paper"
                        ][:5],
                    )
                    gaps.append(gap)

        return gaps
