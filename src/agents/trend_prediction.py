"""
ResearchAI - Trend Prediction Agent
Predicts emerging research trends using citation network analysis.
Lightweight approach: citation velocity + topic growth + exponential smoothing.
No GPU required for initial prototype.
"""

import uuid
import math
from collections import defaultdict
from typing import Optional

from src.agents.base_agent import BaseAgent
from src.models.data_models import TrendPrediction


class TrendPredictionAgent(BaseAgent):
    """Predicts emerging research topics using temporal graph analysis.

    Metrics (all computed with free Python libraries):
        1. Citation velocity: citations/year acceleration
        2. Topic growth rate: new papers/year in topic area
        3. Graph centrality trends: PageRank change over time
        4. Author mobility: new authors entering a topic
        5. Exponential smoothing for future projections

    No GPU or paid API required — pure NetworkX + Python math.
    """

    def __init__(self, **kwargs):
        super().__init__(name="trend_prediction", **kwargs)

    # ── Main Entry Point ─────────────────────────────────────────────

    def process(
        self,
        time_horizon: str = "5_years",
        top_n: int = 10,
    ) -> list[TrendPrediction]:
        """Predict emerging research topics.

        Args:
            time_horizon: "5_years" or "10_years".
            top_n: Number of top trends to return.

        Returns:
            Ranked list of TrendPrediction objects.
        """
        # 1. Compute topic time-series metrics
        topic_metrics = self._compute_topic_metrics()

        if not topic_metrics:
            self.logger.warning("No topic data available for trend prediction")
            return []

        # 2. Apply exponential smoothing for prediction
        predictions = []
        for topic, metrics in topic_metrics.items():
            prediction = self._predict_topic(topic, metrics, time_horizon)
            if prediction:
                predictions.append(prediction)

        # 3. Rank by confidence score
        predictions.sort(key=lambda p: p.confidence_score, reverse=True)

        # Assign ranks
        for i, pred in enumerate(predictions):
            pred.prediction_id = f"trend_{i+1}_{uuid.uuid4().hex[:6]}"

        self.logger.info(f"Generated {len(predictions)} trend predictions")
        return predictions[:top_n]

    # ── Metric Computation ───────────────────────────────────────────

    def _compute_topic_metrics(self) -> dict[str, dict]:
        """Compute temporal metrics for each topic in the knowledge graph."""
        topic_metrics = {}

        # Get all topics
        topics = self.kg.get_nodes_by_type("topic")
        papers = self.kg.get_nodes_by_type("paper")

        if not topics or not papers:
            return {}

        # Build topic → papers mapping with years
        topic_papers = defaultdict(list)
        for paper in papers:
            year = paper.get("year", 0)
            if not year:
                continue
            neighbors = self.kg.get_neighbors(paper["id"])
            for n in neighbors:
                if n.get("node_type") == "topic":
                    topic_name = n.get("name", n["id"])
                    topic_papers[topic_name].append({
                        "paper_id": paper["id"],
                        "year": year,
                        "citations": paper.get("citation_count", 0),
                    })

        # Compute metrics per topic
        for topic_name, papers_list in topic_papers.items():
            if len(papers_list) < 2:
                continue

            years = sorted(set(p["year"] for p in papers_list))
            if len(years) < 2:
                continue

            # Papers per year
            papers_per_year = defaultdict(int)
            citations_per_year = defaultdict(int)
            for p in papers_list:
                papers_per_year[p["year"]] += 1
                citations_per_year[p["year"]] += p["citations"]

            # Growth rate (papers/year slope)
            growth_rate = self._compute_growth_rate(papers_per_year, years)

            # Citation velocity (citations/year acceleration)
            citation_velocity = self._compute_citation_velocity(citations_per_year, years)

            # Recency score (proportion of papers in recent years)
            total = len(papers_list)
            median_year = years[len(years) // 2]
            recent = sum(1 for p in papers_list if p["year"] >= median_year)
            recency_score = recent / total

            # Author diversity (unique authors)
            author_count = self._count_topic_authors(topic_name)

            topic_metrics[topic_name] = {
                "total_papers": total,
                "years": years,
                "papers_per_year": dict(papers_per_year),
                "citations_per_year": dict(citations_per_year),
                "growth_rate": growth_rate,
                "citation_velocity": citation_velocity,
                "recency_score": recency_score,
                "author_count": author_count,
                "latest_year": max(years),
            }

        return topic_metrics

    def _compute_growth_rate(
        self, papers_per_year: dict[int, int], years: list[int]
    ) -> float:
        """Compute papers/year growth rate using simple linear regression."""
        if len(years) < 2:
            return 0.0

        n = len(years)
        x_mean = sum(years) / n
        y_values = [papers_per_year.get(y, 0) for y in years]
        y_mean = sum(y_values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(years, y_values))
        denominator = sum((x - x_mean) ** 2 for x in years)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _compute_citation_velocity(
        self, citations_per_year: dict[int, int], years: list[int]
    ) -> float:
        """Compute citation acceleration (change in citations/year)."""
        if len(years) < 3:
            return 0.0

        # Compute year-over-year changes
        changes = []
        for i in range(1, len(years)):
            prev = citations_per_year.get(years[i - 1], 0)
            curr = citations_per_year.get(years[i], 0)
            if prev > 0:
                changes.append((curr - prev) / prev)

        if not changes:
            return 0.0

        return sum(changes) / len(changes)

    def _count_topic_authors(self, topic_name: str) -> int:
        """Count unique authors working on a topic."""
        topic_nodes = self.kg.search_nodes(topic_name, node_type="topic")
        author_ids = set()

        for topic_node in topic_nodes:
            # Topic → Paper → Author
            neighbors = self.kg.get_neighbors(topic_node["id"])
            for n in neighbors:
                if n.get("node_type") == "paper":
                    paper_neighbors = self.kg.get_neighbors(n["id"], "authored_by")
                    for author in paper_neighbors:
                        author_ids.add(author["id"])

        return len(author_ids)

    # ── Prediction ───────────────────────────────────────────────────

    def _predict_topic(
        self,
        topic: str,
        metrics: dict,
        time_horizon: str,
    ) -> Optional[TrendPrediction]:
        """Generate a trend prediction for a single topic."""

        # Apply exponential smoothing to project future growth
        papers_per_year = metrics["papers_per_year"]
        years = metrics["years"]
        projected = self._exponential_smoothing(papers_per_year, years)

        # Compute confidence score (0-1) from multiple signals
        confidence = self._compute_confidence(metrics, projected)

        if confidence < 0.1:
            return None

        # Generate description
        description = self._generate_description(topic, metrics, projected, time_horizon)

        # Gather supporting evidence (paper IDs)
        evidence = self._get_evidence_papers(topic)

        return TrendPrediction(
            prediction_id="",  # Set by caller
            topic=topic,
            description=description,
            confidence_score=round(confidence, 3),
            time_horizon=time_horizon,
            supporting_evidence=evidence,
            growth_rate=round(metrics["growth_rate"], 3),
            citation_velocity=round(metrics["citation_velocity"], 3),
            current_paper_count=metrics["total_papers"],
        )

    def _exponential_smoothing(
        self,
        papers_per_year: dict[int, int],
        years: list[int],
        alpha: float = 0.3,
        forecast_years: int = 5,
    ) -> dict[int, float]:
        """Simple exponential smoothing to project future paper counts.

        Args:
            papers_per_year: Historical paper counts.
            years: Sorted list of years.
            alpha: Smoothing factor (0-1, higher = more weight on recent).
            forecast_years: Number of years to forecast.

        Returns:
            Dict of year → projected paper count.
        """
        if not years:
            return {}

        # Initialize with first value
        values = [papers_per_year.get(y, 0) for y in years]
        smoothed = values[0]

        # Apply exponential smoothing
        for v in values[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed

        # Project forward
        last_year = max(years)
        projections = {}
        trend = values[-1] - values[0] if len(values) > 1 else 0
        trend_per_year = trend / max(len(years) - 1, 1)

        for i in range(1, forecast_years + 1):
            projected_year = last_year + i
            projected_value = smoothed + trend_per_year * i
            projections[projected_year] = max(0, projected_value)

        return projections

    def _compute_confidence(self, metrics: dict, projected: dict) -> float:
        """Compute a confidence score based on multiple signals."""
        scores = []

        # 1. Growth rate signal (higher growth → higher confidence)
        growth = metrics["growth_rate"]
        growth_score = min(1.0, max(0.0, growth / 5.0)) if growth > 0 else 0
        scores.append(growth_score * 0.3)

        # 2. Citation velocity signal
        velocity = metrics["citation_velocity"]
        velocity_score = min(1.0, max(0.0, velocity)) if velocity > 0 else 0
        scores.append(velocity_score * 0.25)

        # 3. Recency signal (high recent activity)
        recency = metrics["recency_score"]
        scores.append(recency * 0.2)

        # 4. Volume signal (enough papers for reliable prediction)
        total = metrics["total_papers"]
        volume_score = min(1.0, total / 20.0)
        scores.append(volume_score * 0.15)

        # 5. Author diversity signal
        authors = metrics["author_count"]
        diversity_score = min(1.0, authors / 10.0)
        scores.append(diversity_score * 0.1)

        return sum(scores)

    # ── Description Generation ───────────────────────────────────────

    def _generate_description(
        self,
        topic: str,
        metrics: dict,
        projected: dict,
        time_horizon: str,
    ) -> str:
        """Generate a human-readable trend description."""
        horizon_years = 5 if "5" in time_horizon else 10
        total = metrics["total_papers"]
        growth = metrics["growth_rate"]

        description = f"'{topic}' shows "

        if growth > 2:
            description += "strong upward momentum"
        elif growth > 0.5:
            description += "steady growth"
        elif growth > 0:
            description += "modest emerging activity"
        else:
            description += "early-stage potential"

        description += f" with {total} papers tracked."

        if projected:
            future_years = sorted(projected.keys())
            if future_years:
                last_projected = projected[future_years[-1]]
                description += (
                    f" Projected to reach ~{int(last_projected)} papers/year "
                    f"by {future_years[-1]}."
                )

        if metrics["author_count"] > 5:
            description += f" Active community of {metrics['author_count']}+ researchers."

        return description

    def _get_evidence_papers(self, topic: str) -> list[str]:
        """Get paper IDs related to this topic."""
        topic_nodes = self.kg.search_nodes(topic, node_type="topic")
        paper_ids = []
        for node in topic_nodes:
            neighbors = self.kg.get_neighbors(node["id"])
            for n in neighbors:
                if n.get("node_type") == "paper":
                    paper_ids.append(n["id"])
        return paper_ids[:10]
