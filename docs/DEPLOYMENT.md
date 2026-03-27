# Deployment Guide - ResearchAI

## 🌎 Option 1: Hugging Face Spaces (Recommended)
1. **Create Space**: Go to [Hugging Face Spaces](https://huggingface.co/new-space).
2. **Settings**:
   - **SDK**: Streamlit
   - **Python**: 3.10
   - **Hardware**: CPU basic (Free)
3. **Upload Files**: Upload all project files to the repository.
   - Ensure `requirements.txt` and `packages.txt` are at the root.
4. **App Entry**: HF will automatically detect `app.py` if it's at the root. 
   - *Note*: I recommend creating a small `app.py` at the root that imports and runs `dashboard/app.py`.

## ☁️ Option 2: Streamlit Community Cloud
1. Connect your GitHub repository to [Streamlit Cloud](https://share.streamlit.io/).
2. Set the main file path to `dashboard/app.py`.
3. The platform will automatically install dependencies from `requirements.txt`.

## 🛠️ Performance Optimizations
- **Lazy Loading**: ScispaCy and BART models only load when a synthesis is triggered.
- **Memory Management**: The system processes text in chunks to avoid OOM in free-tier environments.
- **Model Storage**: Hugging Face Spaces has persistent storage; models will be cached after the first run.
