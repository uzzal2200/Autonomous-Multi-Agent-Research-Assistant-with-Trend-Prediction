"""Integration tests for AgentOrchestrator."""

from unittest.mock import patch, MagicMock
import pytest
from src.orchestrator.agent_orchestrator import AgentOrchestrator

class TestAgentOrchestrator:
    @patch('src.orchestrator.agent_orchestrator.PaperRetrievalAgent')
    @patch('src.orchestrator.agent_orchestrator.KnowledgeExtractionAgent')
    @patch('src.orchestrator.agent_orchestrator.GapDetectionAgent')
    @patch('src.orchestrator.agent_orchestrator.ExperimentSuggestionAgent')
    @patch('src.orchestrator.agent_orchestrator.SummarizationAgent')
    @patch('src.orchestrator.agent_orchestrator.TrendPredictionAgent')
    def test_run_full_pipeline(self, mock_trend, mock_summ, mock_exp, mock_gap, mock_kg, mock_paper):
        # Setup mocks
        mock_paper.return_value.run.return_value = {"result": [{"title": "mock paper"}]}
        mock_kg.return_value.run.return_value = {"result": True}
        mock_gap.return_value.run.return_value = {"result": [{"gap": "mock gap"}]}
        mock_exp.return_value.run.return_value = {"result": [{"exp": "mock exp"}]}
        mock_summ.return_value.run.return_value = {"result": [{"sum": "mock sum"}]}
        mock_trend.return_value.run.return_value = {"result": [{"trend": "mock trend"}]}
        
        orchestrator = AgentOrchestrator()
        
        # Override agents to use mocks
        orchestrator.paper_agent = mock_paper.return_value
        orchestrator.knowledge_agent = mock_kg.return_value
        orchestrator.gap_agent = mock_gap.return_value
        orchestrator.experiment_agent = mock_exp.return_value
        orchestrator.summary_agent = mock_summ.return_value
        orchestrator.trend_agent = mock_trend.return_value

        # Need to mock the KnowledgeGraphManager.save method that gets called at the end
        orchestrator.kg = MagicMock()

        result = orchestrator.run_full_pipeline("test query")
        
        assert "stages" in result
        assert "paper_retrieval" in result["stages"]
        assert result["stages"]["paper_retrieval"]["result"][0]["title"] == "mock paper"
        
        orchestrator.paper_agent.run.assert_called_once()
        orchestrator.knowledge_agent.run.assert_called_once()
        orchestrator.gap_agent.run.assert_called_once()
        orchestrator.experiment_agent.run.assert_called_once()
        orchestrator.summary_agent.run.assert_called_once()
        orchestrator.trend_agent.run.assert_called_once()
        orchestrator.kg.save.assert_called_once()

    def test_run_empty_pipeline(self):
        """Test pipeline behavior when paper retrieval returns empty."""
        orchestrator = AgentOrchestrator()
        
        # Mock paper agent to return empty list
        mock_paper = MagicMock()
        mock_paper.run.return_value = {"result": []}
        orchestrator.paper_agent = mock_paper
        
        # Replace other agents with mocks to ensure they aren't called
        orchestrator.knowledge_agent = MagicMock()
        orchestrator.gap_agent = MagicMock()
        
        result = orchestrator.run_full_pipeline("test query")
        
        assert "stages" in result
        assert "paper_retrieval" in result["stages"]
        
        # Knowledge agent shouldn't be called if no papers are retrieved
        orchestrator.knowledge_agent.run.assert_not_called()
        orchestrator.gap_agent.run.assert_not_called()
