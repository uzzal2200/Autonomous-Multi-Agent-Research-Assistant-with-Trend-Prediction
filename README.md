# 🔬 ResearchAI – Autonomous Multi-Agent Research Assistant

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Free & Open Source](https://img.shields.io/badge/Cost-100%25%20Free-brightgreen.svg)]()

**ResearchAI** is a modular, multi-agent AI platform that helps students and researchers:

- 📄 **Discover & retrieve** papers from arXiv, Semantic Scholar, and PubMed
- 🧠 **Extract knowledge** and build research knowledge graphs
- 🔍 **Detect research gaps** — underexplored areas, contradictions, missing methods
- 🧪 **Suggest experiments** with hypotheses, datasets, and methodology
- 📝 **Summarize papers** using free AI models (BART-CNN)
- 📈 **Predict emerging trends** using citation network analysis

> **100% free and open-source.** No paid APIs required. Runs entirely on your machine.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                        │
│  Paper Explorer │ Knowledge Graph │ Gaps │ Experiments │ Trends│
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   Agent Orchestrator                          │
│  Coordinates multi-agent pipelines (full, summary, gap, trend)│
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                      Agents Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Paper    │ │Knowledge │ │   Gap    │ │Experiment│        │
│  │Retrieval │ │Extraction│ │Detection │ │Suggestion│        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐                                   │
│  │Summarize │ │  Trend   │                                   │
│  │  Agent   │ │Prediction│                                   │
│  └──────────┘ └──────────┘                                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    Storage Layer                              │
│  NetworkX KG │ ChromaDB Vectors │ SQLite Cache               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd "c:\Projects\AI-Research-Assistant--main"
pip install -r requirements.txt
```

### 2. Configure (Optional)

```bash
copy .env.example .env
# Edit .env to add Semantic Scholar API key (optional, for higher rate limits)
```

### 3. Run Dashboard

```bash
streamlit run dashboard/app.py
```

The app will open in your browser at `http://localhost:8501`.

### Dashboard UI

The Streamlit dashboard features a modern, professional design:

- **Color theme**: Indigo accent (#6366f1), dark background, high-contrast text
- **Typography**: Outfit for headings, Inter for body text
- **Glass-style cards**: Semi-transparent panels with subtle borders
- **Empty states**: Clear prompts when data is missing
- **Loading states**: Spinners and progress for pipeline execution
- **Interactive charts**: PyVis knowledge graph, Plotly trend scatter plots

### 4. Demo Mode

Click **"Load Pre-computed Demo Dataset 📦"** on the Deep Search page to explore the dashboard with 20 pre-loaded papers, knowledge graph, gaps, experiments, and trends — no API calls needed.

### 5. Full Pipeline

Enter a research topic (e.g., *"Graph Neural Networks"*) and click **"Synthesize Knowledge ▸"** to:
1. Fetch papers from arXiv & Semantic Scholar
2. Build a knowledge graph
3. Detect research gaps
4. Generate experiment suggestions
5. Predict emerging trends

---

## 📂 Project Structure

```
AI Research Assistant/
├── config/settings.py          # Central configuration
├── src/
│   ├── agents/                 # 6 specialized agents
│   │   ├── base_agent.py       # Abstract base class
│   │   ├── paper_retrieval.py  # arXiv, Semantic Scholar, PubMed
│   │   ├── knowledge_extraction.py
│   │   ├── gap_detection.py    # 4 gap-finding strategies
│   │   ├── experiment_suggestion.py
│   │   ├── summarization.py    # BART-CNN + map-reduce
│   │   └── trend_prediction.py # Exponential smoothing + multi-signal
│   ├── orchestrator/           # Multi-agent pipeline coordinator
│   ├── knowledge_graph/        # NetworkX graph manager
│   ├── vector_store/           # ChromaDB embeddings
│   ├── models/                 # Pydantic data models
│   └── utils/                  # Logger, PDF parser, NLP tools
├── dashboard/app.py            # Streamlit interactive dashboard
├── data/                       # Sample papers + citation network
├── tests/                      # Unit tests
└── docs/                       # Architecture documentation
```

---

## 🤖 Agents

| Agent | Purpose | Technology |
|-------|---------|------------|
| **Paper Retrieval** | Fetch papers from 3 APIs | arXiv, Semantic Scholar, PubMed (all free) |
| **Knowledge Extraction** | Extract entities & relations | NLP patterns, keyword extraction, NER |
| **Gap Detection** | Find underexplored areas | Graph topology analysis (4 strategies) |
| **Experiment Suggestion** | Propose experiments | RAG + template generation (flan-t5-base) |
| **Summarization** | Summarize papers | facebook/bart-large-cnn (free, local) |
| **Trend Prediction** | Predict emerging topics | Citation velocity + exponential smoothing |

---

## 💡 Free Tech Stack

| Component | Technology | Cost |
|-----------|------------|------|
| Summarization | facebook/bart-large-cnn | Free |
| Embeddings | all-MiniLM-L6-v2 | Free |
| Text Generation | google/flan-t5-base | Free |
| Vector Store | ChromaDB | Free |
| Knowledge Graph | NetworkX | Free |
| Paper APIs | arXiv, Semantic Scholar, PubMed | Free |
| Dashboard | Streamlit + Plotly + PyVis | Free |
| PDF Parsing | PyPDF2 + BeautifulSoup | Free |

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

## ⚠️ Troubleshooting

- **ModuleNotFoundError**: Ensure you run commands from the project root and have installed dependencies: `pip install -r requirements.txt`
- **CUDA/GPU**: The app runs on CPU by default. Set `USE_GPU=true` in `.env` for GPU acceleration (requires CUDA).
- **First run**: Downloading HuggingFace models (BART, sentence-transformers) may take several minutes on first use.
- **Demo mode**: Use "Load Pre-computed Demo Dataset" to explore without API calls or model downloads.

---

## 📈 Advanced Concepts Demonstrated

- **Multi-agent AI systems** — 6 specialized agents with shared context
- **Knowledge graph reasoning** — NetworkX with centrality, community detection
- **Retrieval-augmented generation (RAG)** — ChromaDB + sentence-transformers
- **NLP-based summarization** — BART-CNN abstractive summarization
- **Research gap detection** — Graph topology + temporal analysis
- **Scientific trend prediction** — Citation network temporal analysis
- **Interactive visualization** — Streamlit + PyVis + Plotly

---

## 📝 License

MIT License — Free for academic and commercial use.
