# ResearchAI - Agents Package
from .base_agent import BaseAgent
from .paper_retrieval import PaperRetrievalAgent
from .knowledge_extraction import KnowledgeExtractionAgent
from .gap_detection import GapDetectionAgent
from .experiment_suggestion import ExperimentSuggestionAgent
from .summarization import SummarizationAgent
from .trend_prediction import TrendPredictionAgent

__all__ = [
    "BaseAgent",
    "PaperRetrievalAgent",
    "KnowledgeExtractionAgent",
    "GapDetectionAgent",
    "ExperimentSuggestionAgent",
    "SummarizationAgent",
    "TrendPredictionAgent",
]
