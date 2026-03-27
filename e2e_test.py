import json
from src.orchestrator.agent_orchestrator import AgentOrchestrator

def main():
    print("Initializing Agent Orchestrator...")
    orchestrator = AgentOrchestrator()
    
    query = "graph neural networks applications"
    print(f"Running full pipeline for query: '{query}'")
    
    # We use a small number of max papers to speed up the test
    results = orchestrator.run_full_pipeline(query=query, max_papers=2)
    
    print("\n================ E2E Test Results ================\n")
    print(f"Query: {results['query']}")
    print(f"Papers retrieved: {len(results['stages'].get('paper_retrieval', {}).get('result', []))}")
    print(f"Gaps identified: {len(results['stages'].get('gap_detection', {}).get('result', []))}")
    print(f"Experiments suggested: {len(results['stages'].get('experiment_suggestion', {}).get('result', []))}")
    print(f"Trends predicted: {len(results['stages'].get('trend_prediction', {}).get('result', []))}")
    
    print("\nE2E Pipeline execution successful!")

if __name__ == "__main__":
    main()
