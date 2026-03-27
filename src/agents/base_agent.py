"""
ResearchAI - Base Agent
Abstract base class defining the common interface for all agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.knowledge_graph.graph_manager import KnowledgeGraphManager
from src.vector_store.chroma_store import VectorStoreManager
from src.utils.logger import get_logger


class BaseAgent(ABC):
    """Abstract base class for all ResearchAI agents.

    Provides shared access to the knowledge graph, vector store,
    and structured logging. Each agent must implement process().
    """

    def __init__(
        self,
        name: str,
        knowledge_graph: Optional[KnowledgeGraphManager] = None,
        vector_store: Optional[VectorStoreManager] = None,
    ):
        self.name = name
        self.kg = knowledge_graph or KnowledgeGraphManager()
        self.vs = vector_store or VectorStoreManager()
        self.logger = get_logger(name)

    @abstractmethod
    def process(self, **kwargs) -> Any:
        """Execute the agent's main task.

        Each agent implements its specific processing logic here.

        Returns:
            Agent-specific output (papers, gaps, summaries, etc.)
        """
        pass

    def run(self, **kwargs) -> dict:
        """Run the agent with error handling and reporting.

        Returns:
            Dict with 'status', 'agent', 'result' or 'error' keys.
        """
        self.logger.info(f"Agent '{self.name}' starting...")
        try:
            result = self.process(**kwargs)
            self.logger.info(f"Agent '{self.name}' completed successfully.")
            return {
                "status": "success",
                "agent": self.name,
                "result": result,
            }
        except Exception as e:
            self.logger.error(f"Agent '{self.name}' failed: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
            }

    def report(self) -> str:
        """Generate a human-readable status report for this agent."""
        return f"Agent: {self.name} | Status: ready"
