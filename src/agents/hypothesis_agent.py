"""
ResearchAI - Hypothesis Generation Agent
Formulates formal research hypotheses based on detected gaps.
"""

from typing import List
from src.agents.base_agent import BaseAgent
from src.models.data_models import ResearchGap

class HypothesisGenerationAgent(BaseAgent):
    """Generates testable hypotheses from identified gaps."""

    def __init__(self, **kwargs):
        super().__init__(name="hypothesis_generation", **kwargs)

    def process(self, gaps: List[ResearchGap]) -> List[dict]:
        """Convert research gaps into structured hypotheses.
        
        Args:
            gaps: List of ResearchGap objects.
            
        Returns:
            List of dicts with title, hypothesis, and rationale.
        """
        hypotheses = []
        for gap in gaps:
            h = {
                "title": f"Hypothesis on {gap.topic[:30]}...",
                "gap_ref": gap.topic,
                "hypothesis": f"It is hypothesized that addressing the {gap.gap_type} in {gap.topic} using integrated cross-domain methods will yield significant improvements.",
                "rationale": f"Based on identified gaps: {gap.description}",
                "novelty_score": gap.novelty_score
            }
            hypotheses.append(h)
            
        return hypotheses
