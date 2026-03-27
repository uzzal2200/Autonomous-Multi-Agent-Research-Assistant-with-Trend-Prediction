"""
ResearchAI - Agent Orchestrator
Coordinates multi-agent pipelines for research analysis.
"""

from typing import Optional

from src.agents.paper_retrieval import PaperRetrievalAgent
from src.agents.knowledge_extraction import KnowledgeExtractionAgent
from src.agents.gap_detection import GapDetectionAgent
from src.agents.experiment_suggestion import ExperimentSuggestionAgent
from src.agents.summarization import SummarizationAgent
from src.agents.trend_prediction import TrendPredictionAgent
from src.knowledge_graph.graph_manager import KnowledgeGraphManager
from src.vector_store.chroma_store import VectorStoreManager
from src.utils.logger import get_logger

logger = get_logger("orchestrator")


class AgentOrchestrator:
    """Coordinates multiple agents to form research analysis pipelines.

    Pipelines:
        - full: Paper retrieval → Knowledge extraction → Gap detection
                → Experiment suggestion → Summarization → Trend prediction
        - summary_only: Paper retrieval → Summarization
        - gaps_only: (uses existing KG) → Gap detection → Experiment suggestion
        - trends_only: (uses existing KG) → Trend prediction

    All agents share the same KnowledgeGraph and VectorStore instances.
    """

    def __init__(self):
        # Shared storage
        self.kg = KnowledgeGraphManager()
        self.vs = VectorStoreManager()

        # Initialize agents with shared storage
        self.paper_agent = PaperRetrievalAgent(
            knowledge_graph=self.kg, vector_store=self.vs
        )
        self.knowledge_agent = KnowledgeExtractionAgent(
            knowledge_graph=self.kg, vector_store=self.vs
        )
        self.gap_agent = GapDetectionAgent(
            knowledge_graph=self.kg, vector_store=self.vs
        )
        self.experiment_agent = ExperimentSuggestionAgent(
            knowledge_graph=self.kg, vector_store=self.vs
        )
        self.summary_agent = SummarizationAgent(
            knowledge_graph=self.kg, vector_store=self.vs
        )
        self.trend_agent = TrendPredictionAgent(
            knowledge_graph=self.kg, vector_store=self.vs
        )

        logger.info("Orchestrator initialized with all agents")

    # ── Full Pipeline ────────────────────────────────────────────────

    def run_full_pipeline(
        self,
        query: str,
        max_papers: int = 20,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        sources: Optional[list[str]] = None,
    ) -> dict:
        """Run the complete research analysis pipeline.

        Steps:
            1. Fetch papers matching the query
            2. Extract knowledge and build graph
            3. Detect research gaps
            4. Suggest experiments for gaps
            5. Summarize papers
            6. Predict emerging trends

        Args:
            query: Research topic query.
            max_papers: Max papers to retrieve.
            year_from: Filter start year.
            year_to: Filter end year.
            sources: API sources to use.

        Returns:
            Dict with results from each stage.
        """
        results = {"query": query, "stages": {}}

        # Stage 1: Paper Retrieval
        logger.info(f"[Pipeline] Stage 1/6: Retrieving papers for '{query}'")
        paper_result = self.paper_agent.run(
            query=query,
            max_results=max_papers,
            year_from=year_from,
            year_to=year_to,
            sources=sources,
        )
        results["stages"]["paper_retrieval"] = paper_result
        papers = paper_result.get("result", [])

        if not papers:
            logger.warning("No papers retrieved. Pipeline stopping.")
            return results

        # Stage 2: Knowledge Extraction
        logger.info(f"[Pipeline] Stage 2/6: Extracting knowledge from {len(papers)} papers")
        knowledge_result = self.knowledge_agent.run(papers=papers)
        results["stages"]["knowledge_extraction"] = knowledge_result

        # Stage 3: Gap Detection
        logger.info("[Pipeline] Stage 3/6: Detecting research gaps")
        gap_result = self.gap_agent.run(top_n=10)
        results["stages"]["gap_detection"] = gap_result
        gaps = gap_result.get("result", [])

        # Stage 4: Experiment Suggestions
        logger.info(f"[Pipeline] Stage 4/6: Generating experiment suggestions for {len(gaps)} gaps")
        experiment_result = self.experiment_agent.run(gaps=gaps)
        results["stages"]["experiment_suggestion"] = experiment_result

        # Stage 5: Summarization
        logger.info(f"[Pipeline] Stage 5/6: Summarizing {len(papers)} papers")
        summary_result = self.summary_agent.run(papers=papers, mode="single")
        results["stages"]["summarization"] = summary_result

        # Stage 6: Trend Prediction
        logger.info("[Pipeline] Stage 6/6: Predicting research trends")
        trend_result = self.trend_agent.run(top_n=10)
        results["stages"]["trend_prediction"] = trend_result

        # Save knowledge graph
        self.kg.save()

        logger.info(
            f"[Pipeline] Complete! Papers: {len(papers)}, "
            f"Gaps: {len(gaps)}, "
            f"Experiments: {len(experiment_result.get('result', []))}, "
            f"Trends: {len(trend_result.get('result', []))}"
        )

        return results

    # ── Partial Pipelines ────────────────────────────────────────────

    def run_summary_pipeline(
        self,
        query: str,
        max_papers: int = 10,
        mode: str = "single",
    ) -> dict:
        """Fetch papers and generate summaries only."""
        papers = self.paper_agent.process(query=query, max_results=max_papers)
        summaries = self.summary_agent.process(papers=papers, mode=mode)
        return {"papers": papers, "summaries": summaries}

    def run_gap_pipeline(self, top_n: int = 10) -> dict:
        """Run gap detection and experiment suggestion on existing graph."""
        self.kg.load()
        gaps = self.gap_agent.process(top_n=top_n)
        experiments = self.experiment_agent.process(gaps=gaps)
        return {"gaps": gaps, "experiments": experiments}

    def run_trend_pipeline(self, top_n: int = 10) -> dict:
        """Run trend prediction on existing graph."""
        self.kg.load()
        predictions = self.trend_agent.process(top_n=top_n)
        return {"predictions": predictions}

    # ── Graph Management ─────────────────────────────────────────────

    def load_graph(self) -> dict:
        """Load existing knowledge graph and return stats."""
        self.kg.load()
        return self.kg.get_stats()

    def get_graph_stats(self) -> dict:
        """Get current knowledge graph statistics."""
        return self.kg.get_stats()
