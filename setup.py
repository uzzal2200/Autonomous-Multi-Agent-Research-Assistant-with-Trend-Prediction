from setuptools import setup, find_packages

setup(
    name="researchai",
    version="1.0.0",
    description="ResearchAI - Autonomous Multi-Agent Research Assistant with Trend Prediction",
    author="MD Uzzal Mia",
    python_requires=">=3.9",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "transformers>=4.36.0",
        "torch>=2.1.0",
        "sentence-transformers>=2.2.2",
        "chromadb>=0.4.22",
        "networkx>=3.2",
        "arxiv>=2.1.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "PyPDF2>=3.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "streamlit>=1.29.0",
        "streamlit-extras>=0.4.0",
        "plotly>=5.18.0",
        "pyvis>=0.3.2",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "pytest-asyncio>=0.23.0"],
    },
)
