"""
ResearchAI - Paper Retrieval Agent
Fetches papers from arXiv, Semantic Scholar, and PubMed (all free APIs).
Caches results locally to avoid repeated API calls.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional

import requests

from src.agents.base_agent import BaseAgent
from src.models.data_models import Paper, Author
from config.settings import api_settings, storage_settings, app_settings


class PaperRetrievalAgent(BaseAgent):
    """Retrieves academic papers from free open-access sources.

    Sources:
        - arXiv API (free, no key required)
        - Semantic Scholar API (free tier, optional key)
        - PubMed Entrez API (free)

    All responses are cached locally in data/cache/ to minimize API calls.
    """

    def __init__(self, **kwargs):
        super().__init__(name="paper_retrieval", **kwargs)
        self._cache_dir = Path(storage_settings.cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ── Main Entry Point ─────────────────────────────────────────────

    def process(
        self,
        query: str,
        max_results: int = 20,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        sources: Optional[list[str]] = None,
        min_citations: int = 0,
    ) -> list[Paper]:
        """Fetch papers matching a query from multiple sources.

        Args:
            query: Research topic or search query.
            max_results: Maximum papers to return per source.
            year_from: Filter papers published after this year.
            year_to: Filter papers published before this year.
            sources: List of sources to query. Default: ["arxiv", "semantic_scholar"].
            min_citations: Minimum citation count filter.

        Returns:
            List of Paper objects.
        """
        sources = sources or ["arxiv", "semantic_scholar"]
        all_papers = []

        if "arxiv" in sources:
            papers = self._fetch_arxiv(query, max_results)
            all_papers.extend(papers)

        if "semantic_scholar" in sources:
            papers = self._fetch_semantic_scholar(query, max_results)
            all_papers.extend(papers)

        if "pubmed" in sources:
            papers = self._fetch_pubmed(query, max_results)
            all_papers.extend(papers)

        # Apply filters
        filtered = self._apply_filters(
            all_papers,
            year_from=year_from,
            year_to=year_to,
            min_citations=min_citations,
        )

        # Deduplicate by title similarity
        deduplicated = self._deduplicate(filtered)

        self.logger.info(
            f"Retrieved {len(deduplicated)} papers for query '{query}' "
            f"(from {len(all_papers)} raw results)"
        )
        return deduplicated[:app_settings.max_papers_per_query]

    # ── arXiv ────────────────────────────────────────────────────────

    def _fetch_arxiv(self, query: str, max_results: int) -> list[Paper]:
        """Fetch papers from arXiv API (completely free)."""
        cache_key = self._cache_key("arxiv", query, max_results)
        cached = self._load_cache(cache_key)
        if cached is not None:
            self.logger.info(f"arXiv cache hit for '{query}'")
            return cached

        try:
            import arxiv

            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            papers = []
            for result in search.results():
                paper = Paper(
                    paper_id=result.entry_id.split("/")[-1],
                    title=result.title,
                    abstract=result.summary,
                    authors=[
                        Author(name=str(a)) for a in result.authors
                    ],
                    year=result.published.year if result.published else None,
                    venue="arXiv",
                    source="arxiv",
                    url=result.entry_id,
                    pdf_url=result.pdf_url,
                    keywords=[cat.replace(".", " ") for cat in (result.categories or [])],
                )
                papers.append(paper)

            self._save_cache(cache_key, papers)
            self.logger.info(f"Fetched {len(papers)} papers from arXiv")
            return papers

        except Exception as e:
            self.logger.error(f"arXiv fetch failed: {e}")
            return []

    # ── Semantic Scholar ─────────────────────────────────────────────

    def _fetch_semantic_scholar(self, query: str, max_results: int) -> list[Paper]:
        """Fetch papers from Semantic Scholar API (free tier)."""
        cache_key = self._cache_key("s2", query, max_results)
        cached = self._load_cache(cache_key)
        if cached is not None:
            self.logger.info(f"Semantic Scholar cache hit for '{query}'")
            return cached

        try:
            url = f"{api_settings.semantic_scholar_base_url}/paper/search"
            headers = {}
            if api_settings.semantic_scholar_api_key:
                headers["x-api-key"] = api_settings.semantic_scholar_api_key

            params = {
                "query": query,
                "limit": min(max_results, 100),
                "fields": "paperId,title,abstract,authors,year,venue,citationCount,references,url",
            }

            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("data", []):
                paper = Paper(
                    paper_id=item.get("paperId", ""),
                    title=item.get("title", ""),
                    abstract=item.get("abstract", "") or "",
                    authors=[
                        Author(name=a.get("name", ""), author_id=a.get("authorId"))
                        for a in (item.get("authors") or [])
                    ],
                    year=item.get("year"),
                    venue=item.get("venue", ""),
                    citation_count=item.get("citationCount", 0) or 0,
                    references=[
                        ref.get("paperId", "")
                        for ref in (item.get("references") or [])
                        if ref.get("paperId")
                    ],
                    source="semantic_scholar",
                    url=item.get("url", ""),
                )
                papers.append(paper)

            self._save_cache(cache_key, papers)
            self.logger.info(f"Fetched {len(papers)} papers from Semantic Scholar")

            # Rate limiting for free tier (100 requests/5 min)
            time.sleep(0.5)
            return papers

        except Exception as e:
            self.logger.error(f"Semantic Scholar fetch failed: {e}")
            return []

    # ── PubMed ───────────────────────────────────────────────────────

    def _fetch_pubmed(self, query: str, max_results: int) -> list[Paper]:
        """Fetch papers from PubMed Entrez API (free)."""
        cache_key = self._cache_key("pubmed", query, max_results)
        cached = self._load_cache(cache_key)
        if cached is not None:
            self.logger.info(f"PubMed cache hit for '{query}'")
            return cached

        try:
            # Step 1: Search for paper IDs
            search_url = f"{api_settings.pubmed_base_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
            }
            if api_settings.pubmed_email:
                search_params["email"] = api_settings.pubmed_email

            resp = requests.get(search_url, params=search_params, timeout=30)
            resp.raise_for_status()
            ids = resp.json().get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            # Step 2: Fetch paper details
            fetch_url = f"{api_settings.pubmed_base_url}/esummary.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
            }

            resp = requests.get(fetch_url, params=fetch_params, timeout=30)
            resp.raise_for_status()
            result = resp.json().get("result", {})

            papers = []
            for pmid in ids:
                if pmid not in result:
                    continue
                item = result[pmid]
                paper = Paper(
                    paper_id=f"pubmed_{pmid}",
                    title=item.get("title", ""),
                    abstract="",  # Abstracts require separate efetch call
                    authors=[
                        Author(name=a.get("name", ""))
                        for a in (item.get("authors") or [])
                    ],
                    year=int(item.get("pubdate", "0")[:4]) if item.get("pubdate") else None,
                    venue=item.get("fulljournalname", ""),
                    source="pubmed",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                )
                papers.append(paper)

            self._save_cache(cache_key, papers)
            self.logger.info(f"Fetched {len(papers)} papers from PubMed")
            return papers

        except Exception as e:
            self.logger.error(f"PubMed fetch failed: {e}")
            return []

    # ── Filtering & Deduplication ────────────────────────────────────

    def _apply_filters(
        self,
        papers: list[Paper],
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        min_citations: int = 0,
    ) -> list[Paper]:
        """Apply year and citation filters."""
        filtered = papers
        if year_from:
            filtered = [p for p in filtered if p.year and p.year >= year_from]
        if year_to:
            filtered = [p for p in filtered if p.year and p.year <= year_to]
        if min_citations > 0:
            filtered = [p for p in filtered if p.citation_count >= min_citations]
        return filtered

    def _deduplicate(self, papers: list[Paper]) -> list[Paper]:
        """Remove duplicate papers based on normalized title."""
        seen_titles = set()
        unique = []
        for paper in papers:
            normalized = paper.title.lower().strip()
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(paper)
        return unique

    # ── Caching ──────────────────────────────────────────────────────

    def _cache_key(self, source: str, query: str, max_results: int) -> str:
        raw = f"{source}:{query}:{max_results}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _save_cache(self, key: str, papers: list[Paper]) -> None:
        if not storage_settings.cache_enabled:
            return
        path = self._cache_dir / f"{key}.json"
        data = [p.model_dump(mode="json") for p in papers]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _load_cache(self, key: str) -> Optional[list[Paper]]:
        if not storage_settings.cache_enabled:
            return None
        path = self._cache_dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Paper(**item) for item in data]
        except Exception:
            return None
