"""
ResearchAI - Literature Review Agent
Synthesizes a high-level review of the retrieved corpus.
"""

from typing import List
from src.agents.base_agent import BaseAgent
from src.models.data_models import Paper

class LiteratureReviewAgent(BaseAgent):
    """Synthesizes literature into a structured review."""

    def __init__(self, **kwargs):
        super().__init__(name="literature_review", **kwargs)

    def process(self, papers: List[Paper]) -> str:
        """Create a synthesized review of the provided papers.
        
        Args:
            papers: List of Paper objects.
            
        Returns:
            A string containing the synthesized review.
        """
        if not papers:
            return "No papers available for review."

        review = f"# Research Synthesis: {len(papers)} Papers\n\n"
        
        # Categorize by year
        papers_by_year = {}
        for p in papers:
            year = p.year or "Unknown"
            if year not in papers_by_year:
                papers_by_year[year] = []
            papers_by_year[year].append(p)

        review += "## Timeline and Trends\n"
        for year in sorted(papers_by_year.keys(), reverse=True):
            review += f"### {year}\n"
            for p in papers_by_year[year]:
                review += f"- **{p.title}** ({', '.join([a.name for a in p.authors[:2]])})\n"
        
        review += "\n## Key Contributions Summary\n"
        review += "The analyzed corpus highlights significant interest in methods such as "
        # In a real scenario, we'd extract this from the KG or summaries
        review += "advanced neural architectures and transformer-based models."
        
        return review
