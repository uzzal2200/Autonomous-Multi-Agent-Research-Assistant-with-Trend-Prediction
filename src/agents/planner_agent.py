"""
ResearchAI - Research Planner Agent
Decomposes a research query into a structured multi-step plan.
"""

from typing import List, Dict
from src.agents.base_agent import BaseAgent

class ResearchPlannerAgent(BaseAgent):
    """Plans research steps based on a user query."""

    def __init__(self, **kwargs):
        super().__init__(name="research_planner", **kwargs)

    def process(self, query: str) -> Dict:
        """Analyze query and generate a research plan.
        
        Args:
            query: The research topic/question.
            
        Returns:
            Dict containing search_terms, focus_areas, and suggested_steps.
        """
        self.logger.info(f"Planning research for: {query}")
        
        # Simple heuristic-based planning for now (can be LLM-driven)
        plan = {
            "search_terms": [query, f"{query} review", f"state of the art {query}"],
            "focus_areas": ["Recent breakthroughs", "Methodological gaps", "Open challenges"],
            "suggested_steps": [
                "Retrieve latest relevant papers from arXiv/PubMed",
                "Extract scientific entities and build knowledge graph",
                "Identify specific research gaps and contradictions",
                "Formulate testable hypotheses and propose experiments"
            ]
        }
        
        return plan
