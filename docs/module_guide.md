# ResearchAI – Module Guide

A module-by-module explanation of the ResearchAI system for portfolio presentation.

---

## 1. `config/settings.py` — Central Configuration

Uses `pydantic-settings` to load environment variables with type validation. Organized into four groups:
- **APISettings** — Endpoints and keys for arXiv, Semantic Scholar, PubMed
- **ModelSettings** — HuggingFace model names (all free/open-source)
- **StorageSettings** — Paths for cache, ChromaDB, knowledge graph
- **AppSettings** — Application-level parameters (chunk sizes, summary lengths)

---

## 2. `src/models/data_models.py` — Pydantic Data Models

Typed data classes shared across all agents:
- **Paper** — Full paper metadata (title, abstract, authors, citations, year)
- **KnowledgeEntity** — Extracted entity (topic, method, dataset)
- **ResearchGap** — Detected gap with novelty score and type
- **ExperimentSuggestion** — Proposed experiment with hypothesis and methodology
- **PaperSummary** — Generated summary with structured sections
- **TrendPrediction** — Predicted topic with confidence and metrics

---

## 3. `src/agents/paper_retrieval.py` — Paper Retrieval Agent

**Purpose:** Fetch papers from free academic APIs.

**Key features:**
- Multi-source: arXiv (python library), Semantic Scholar (REST), PubMed (Entrez)
- Local JSON caching in `data/cache/` — avoids repeated API calls
- Filtering by year, citations, relevance
- Title-based deduplication across sources

---

## 4. `src/agents/knowledge_extraction.py` — Knowledge Extraction Agent

**Purpose:** Turn unstructured paper text into structured knowledge.

**Key features:**
- Keyword and bigram extraction for topic identification
- Regex-based method and dataset name extraction
- Knowledge graph population with typed nodes and edges
- Paper embedding via ChromaDB for downstream RAG

---

## 5. `src/agents/gap_detection.py` — Gap Detection Agent

**Purpose:** Analyze the knowledge graph to find research opportunities.

**4 strategies:**
1. Sparse regions — topics with below-average connections
2. Method-dataset gaps — untested combinations
3. Stagnating topics — declining recent activity
4. Isolated clusters — disconnected communities

Each gap receives a novelty score (0-1) and priority ranking.

---

## 6. `src/agents/experiment_suggestion.py` — Experiment Suggestion Agent

**Purpose:** Generate actionable experiment proposals from detected gaps.

**Key features:**
- RAG pipeline — retrieves relevant context from ChromaDB
- Attempts LLM generation (flan-t5-base, free), falls back to templates
- Structured output: hypothesis, methodology, datasets, variables, outcomes
- Difficulty estimation based on novelty score

---

## 7. `src/agents/summarization.py` — Summarization Agent

**Purpose:** Generate paper summaries using free models.

**Key features:**
- Abstractive summarization with facebook/bart-large-cnn
- Map-reduce multi-document summarization
- Extractive fallback when model unavailable
- Contribution, methodology, results, and limitation extraction

---

## 8. `src/agents/trend_prediction.py` — Trend Prediction Agent

**Purpose:** Predict emerging research topics for the next 5-10 years.

**Key features:**
- Lightweight temporal analysis — no GPU required
- 5 signals: citation velocity, growth rate, recency, volume, author diversity
- Exponential smoothing for future projections
- Multi-signal confidence scoring (weighted combination)

---

## 9. `src/knowledge_graph/graph_manager.py` — Knowledge Graph

**Purpose:** Store and analyze research relationships.

**Key features:**
- NetworkX directed graph with typed nodes and edges
- PageRank centrality analysis
- Community detection (greedy modularity)
- Sparse region finding for gap detection
- JSON serialization for persistence

---

## 10. `src/vector_store/chroma_store.py` — Vector Store

**Purpose:** Embed and search paper text for RAG.

**Key features:**
- ChromaDB with persistent storage
- Sentence-transformers embeddings (all-MiniLM-L6-v2, free)
- Cosine similarity search
- Metadata filtering support

---

## 11. `src/orchestrator/agent_orchestrator.py` — Orchestrator

**Purpose:** Coordinate multi-agent pipelines.

**Pipeline modes:**
- **Full:** All 6 agents in sequence
- **Summary-only:** Paper Retrieval → Summarization
- **Gaps-only:** Gap Detection → Experiment Suggestion
- **Trends-only:** Trend Prediction

All agents share the same KnowledgeGraph and VectorStore instances.

---

## 12. `dashboard/app.py` — Interactive Dashboard

**Purpose:** Visual interface for research exploration.

**Pages:**
- **Home** — Pipeline launcher with demo mode
- **Paper Explorer** — Search, filter, and summarize papers
- **Knowledge Graph** — Interactive PyVis graph visualization
- **Gap Analysis** — Ranked gaps with evidence
- **Experiment Lab** — Experiment cards with markdown export
- **Trend Forecast** — Plotly charts with confidence indicators
