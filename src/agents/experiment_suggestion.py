"""
ResearchAI - Experiment Suggestion Agent
Generates concrete experiment proposals based on detected research gaps.
Uses RAG with local embeddings + free text generation model.
"""

import uuid

from src.agents.base_agent import BaseAgent
from src.models.data_models import ResearchGap, ExperimentSuggestion


class ExperimentSuggestionAgent(BaseAgent):
    """Generates actionable experiment proposals from research gaps.

    Uses RAG (ChromaDB retrieval + template-based generation) to
    produce experiment suggestions including hypotheses, methods,
    datasets, and expected outcomes.

    No paid API required — uses template generation with context retrieval.
    """

    def __init__(self, **kwargs):
        super().__init__(name="experiment_suggestion", **kwargs)
        self._generator = None

    def _get_generator(self):
        """Lazy-load free text generation model for proposal writing."""
        if self._generator is None:
            try:
                from transformers import pipeline
                from config.settings import model_settings
                self._generator = pipeline(
                    "text2text-generation",
                    model=model_settings.text_generation_model,
                    max_length=300,
                    device=-1,
                )
                self.logger.info(f"Text generator loaded: {model_settings.text_generation_model}")
            except Exception as e:
                self.logger.warning(f"Generator not available: {e}. Using template fallback.")
        return self._generator

    # ── Main Entry Point ─────────────────────────────────────────────

    def process(self, gaps: list[ResearchGap]) -> list[ExperimentSuggestion]:
        """Generate experiment suggestions for each detected gap.

        Args:
            gaps: List of ResearchGap objects from Gap Detection Agent.

        Returns:
            List of ExperimentSuggestion objects.
        """
        suggestions = []

        for gap in gaps:
            suggestion = self._generate_suggestion(gap)
            if suggestion:
                suggestions.append(suggestion)

        self.logger.info(f"Generated {len(suggestions)} experiment suggestions from {len(gaps)} gaps")
        return suggestions

    # ── Suggestion Generation ────────────────────────────────────────

    def _generate_suggestion(self, gap: ResearchGap) -> ExperimentSuggestion:
        """Generate an experiment suggestion for a single gap."""

        # 1. Retrieve relevant context from vector store
        context = self._retrieve_context(gap.topic)

        # 2. Generate suggestion using template + optional LLM
        suggestion = self._build_suggestion(gap, context)

        return suggestion

    def _retrieve_context(self, topic: str) -> str:
        """Retrieve relevant paper context from vector store for RAG."""
        try:
            results = self.vs.search(topic, n_results=5)
            context_parts = []
            for r in results:
                title = r["metadata"].get("title", "Unknown")
                text = r["text"][:200]
                context_parts.append(f"[{title}]: {text}")
            return "\n".join(context_parts)
        except Exception as e:
            self.logger.warning(f"Context retrieval failed: {e}")
            return ""

    def _build_suggestion(
        self, gap: ResearchGap, context: str
    ) -> ExperimentSuggestion:
        """Build an experiment suggestion using templates and optional LLM."""

        # Try LLM generation first
        generator = self._get_generator()
        if generator and context:
            try:
                prompt = (
                    f"Given research gap: {gap.description}\n"
                    f"Related work: {context[:500]}\n"
                    f"Suggest a specific experiment with hypothesis and methodology:"
                )
                result = generator(prompt)[0]["generated_text"]
                methodology = result.strip()
            except Exception as e:
                self.logger.debug(f"LLM generation failed, using template: {e}")
                methodology = self._template_methodology(gap)
        else:
            methodology = self._template_methodology(gap)

        # Build structured suggestion
        hypothesis = self._generate_hypothesis(gap)
        datasets = self._suggest_datasets(gap)
        variables = self._suggest_variables(gap)
        outcomes = self._suggest_outcomes(gap)

        return ExperimentSuggestion(
            suggestion_id=f"exp_{uuid.uuid4().hex[:8]}",
            gap_id=gap.gap_id,
            title=f"Experiment: Addressing {gap.topic}",
            hypothesis=hypothesis,
            methodology=methodology,
            recommended_datasets=datasets,
            variables=variables,
            expected_outcomes=outcomes,
            difficulty=self._estimate_difficulty(gap),
        )

    # ── Template Generators ──────────────────────────────────────────

    def _generate_hypothesis(self, gap: ResearchGap) -> str:
        """Generate a testable hypothesis from the gap."""
        templates = {
            "underexplored": (
                f"Applying established methods to the underexplored area of "
                f"'{gap.topic}' will yield competitive or superior results "
                f"compared to existing baselines."
            ),
            "missing_method": (
                f"The untested methods in '{gap.topic}' will demonstrate "
                f"measurable improvements on standard evaluation metrics."
            ),
            "missing_dataset": (
                f"Creating or adapting datasets for '{gap.topic}' will enable "
                f"more rigorous evaluation of existing approaches."
            ),
            "contradictory": (
                f"A controlled study on '{gap.topic}' will resolve existing "
                f"contradictions and identify key factors driving divergent results."
            ),
        }
        return templates.get(gap.gap_type, templates["underexplored"])

    def _template_methodology(self, gap: ResearchGap) -> str:
        """Generate a methodology description from templates."""
        base = (
            f"1. Conduct a systematic review of existing work in '{gap.topic}'.\n"
            f"2. Identify the top-performing methods from related domains.\n"
            f"3. Adapt and apply these methods to the target domain.\n"
            f"4. Establish baselines using standard evaluation protocols.\n"
            f"5. Compare results using appropriate statistical tests.\n"
            f"6. Analyze failure cases and identify improvement opportunities."
        )

        if gap.gap_type == "missing_method":
            base += (
                f"\n7. Benchmark untested methods on established datasets.\n"
                f"8. Report performance across multiple metrics."
            )
        elif gap.gap_type == "underexplored":
            base += (
                f"\n7. Map the research landscape to confirm the gap.\n"
                f"8. Propose new evaluation criteria if existing ones are insufficient."
            )

        return base

    def _suggest_datasets(self, gap: ResearchGap) -> list[str]:
        """Suggest relevant datasets."""
        # Check knowledge graph for datasets related to the topic
        related_datasets = []
        topic_nodes = self.kg.search_nodes(gap.topic, node_type="dataset")
        for node in topic_nodes:
            related_datasets.append(node.get("name", node["id"]))

        if not related_datasets:
            related_datasets = [
                f"Domain-specific benchmark for {gap.topic}",
                "Custom collected dataset",
                "Publicly available repository data",
            ]

        return related_datasets[:5]

    def _suggest_variables(self, gap: ResearchGap) -> list[str]:
        """Suggest experimental variables."""
        base_vars = [
            "Accuracy / F1 / BLEU (task-dependent metric)",
            "Computational cost (FLOPs, time)",
            "Data efficiency (performance vs. training size)",
            "Generalization (cross-dataset evaluation)",
        ]

        if "network" in gap.topic.lower() or "graph" in gap.topic.lower():
            base_vars.append("Graph size scalability")
            base_vars.append("Node/edge classification accuracy")
        if "temporal" in gap.topic.lower() or "time" in gap.topic.lower():
            base_vars.append("Temporal prediction accuracy")
            base_vars.append("Forecasting horizon")

        return base_vars[:6]

    def _suggest_outcomes(self, gap: ResearchGap) -> str:
        """Suggest expected outcomes."""
        return (
            f"Expected to demonstrate measurable progress in '{gap.topic}', "
            f"establish new baselines, and identify promising future directions. "
            f"Results should be reproducible and publishable."
        )

    def _estimate_difficulty(self, gap: ResearchGap) -> str:
        """Estimate experiment difficulty."""
        if gap.novelty_score > 0.8:
            return "hard"
        elif gap.novelty_score > 0.5:
            return "medium"
        return "easy"
