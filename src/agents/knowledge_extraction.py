"""
ResearchAI - Knowledge Extraction Agent
Extracts key entities and relationships from papers.
Populates the knowledge graph and vector store.
Uses free HuggingFace models for NLP.
"""

import re
import hashlib
from typing import Optional

from src.agents.base_agent import BaseAgent
from src.models.data_models import Paper, KnowledgeEntity, KnowledgeRelation
from src.utils.text_processing import clean_text, chunk_text, extract_keywords, extract_bigrams
from config.settings import model_settings


class KnowledgeExtractionAgent(BaseAgent):
    """Extracts structured knowledge from paper text.

    Extracts:
        - Key contributions, methods, datasets, results, limitations
        - Builds knowledge graph nodes and edges
        - Stores paper embeddings in ChromaDB for RAG

    Uses free models:
        - Keyword/keyphrase extraction (frequency + heuristic based)
        - Sentence-transformers for embedding (via VectorStoreManager)
    """

    def __init__(self, **kwargs):
        super().__init__(name="knowledge_extraction", **kwargs)
        self._ner_pipeline = None

    def _get_ner_pipeline(self):
        """Lazy-load a free HuggingFace NER pipeline."""
        if self._ner_pipeline is None:
            try:
                from transformers import pipeline
                self._ner_pipeline = pipeline(
                    "token-classification",
                    model="dslim/bert-base-NER",
                    aggregation_strategy="simple",
                    device=-1,  # CPU by default
                )
                self.logger.info("NER pipeline loaded (dslim/bert-base-NER)")
            except Exception as e:
                self.logger.warning(f"NER pipeline not available: {e}. Using keyword fallback.")
        return self._ner_pipeline

    # ── Main Entry Point ─────────────────────────────────────────────

    def process(self, papers: list[Paper]) -> dict:
        """Extract knowledge from a list of papers.

        Args:
            papers: List of Paper objects with abstracts/full text.

        Returns:
            Dict with 'entities', 'relations', 'papers_processed' counts.
        """
        all_entities = []
        all_relations = []

        for paper in papers:
            text = paper.full_text or paper.abstract
            if not text:
                self.logger.warning(f"Skipping paper '{paper.title}' (no text)")
                continue

            # 1. Add paper to knowledge graph
            self._add_paper_to_graph(paper)

            # 2. Extract entities from text
            entities = self._extract_entities(paper, text)
            all_entities.extend(entities)

            # 3. Build relations
            relations = self._build_relations(paper, entities)
            all_relations.extend(relations)

            # 4. Store paper chunks in vector store for RAG
            self._embed_paper(paper, text)

        self.logger.info(
            f"Extracted {len(all_entities)} entities, {len(all_relations)} relations "
            f"from {len(papers)} papers"
        )

        return {
            "entities": all_entities,
            "relations": all_relations,
            "papers_processed": len(papers),
        }

    # ── Entity Extraction ────────────────────────────────────────────

    def _extract_entities(self, paper: Paper, text: str) -> list[KnowledgeEntity]:
        """Extract knowledge entities from paper text."""
        entities = []
        cleaned = clean_text(text)

        # Extract topics via keywords and bigrams
        keywords = extract_keywords(cleaned, top_n=10)
        bigrams = extract_bigrams(cleaned, top_n=5)

        for kw in keywords:
            entity = KnowledgeEntity(
                entity_id=self._make_id("topic", kw),
                entity_type="topic",
                name=kw,
                source_paper_id=paper.paper_id,
                confidence=0.8,
            )
            entities.append(entity)

        for bg in bigrams:
            entity = KnowledgeEntity(
                entity_id=self._make_id("topic", bg),
                entity_type="topic",
                name=bg,
                source_paper_id=paper.paper_id,
                confidence=0.9,
            )
            entities.append(entity)

        # Extract methods (heuristic patterns)
        methods = self._extract_methods(cleaned)
        for method_name in methods:
            entity = KnowledgeEntity(
                entity_id=self._make_id("method", method_name),
                entity_type="method",
                name=method_name,
                source_paper_id=paper.paper_id,
                confidence=0.75,
            )
            entities.append(entity)

        # Extract datasets (heuristic patterns)
        datasets = self._extract_datasets(cleaned)
        for dataset_name in datasets:
            entity = KnowledgeEntity(
                entity_id=self._make_id("dataset", dataset_name),
                entity_type="dataset",
                name=dataset_name,
                source_paper_id=paper.paper_id,
                confidence=0.7,
            )
            entities.append(entity)

        # Add entities to knowledge graph
        for entity in entities:
            self.kg.add_node(
                entity.entity_id,
                entity.entity_type,
                name=entity.name,
                description=entity.description,
                confidence=entity.confidence,
            )

        return entities

    def _extract_methods(self, text: str) -> list[str]:
        """Extract method names using pattern matching."""
        method_patterns = [
            r"(?:use|propose|employ|apply|implement)\w*\s+([\w\s\-]+?(?:network|model|algorithm|method|approach|framework|architecture|technique))",
            r"((?:convolutional|recurrent|transformer|attention|graph)\s+(?:neural\s+)?network\w*)",
            r"((?:random forest|decision tree|support vector|gradient boosting|logistic regression)\w*)",
            r"((?:BERT|GPT|T5|LSTM|GRU|CNN|RNN|GAN|VAE|GNN)\w*)",
        ]

        methods = set()
        for pattern in method_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip().lower()
                if len(name) > 3 and len(name) < 60:
                    methods.add(name)

        return list(methods)[:10]

    def _extract_datasets(self, text: str) -> list[str]:
        """Extract dataset names using pattern matching."""
        dataset_patterns = [
            r"(?:dataset|benchmark|corpus)\s+(?:called|named)?\s*[\"']?([\w\-]+)[\"']?",
            r"((?:ImageNet|CIFAR|MNIST|COCO|SQuAD|GLUE|SuperGLUE|WikiText|Penn Treebank|CoNLL)\w*)",
            r"(?:evaluate|test|train)\w*\s+on\s+(?:the\s+)?([\w\-]+)\s+dataset",
        ]

        datasets = set()
        for pattern in dataset_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if len(name) > 2 and len(name) < 40:
                    datasets.add(name)

        return list(datasets)[:10]

    # ── Relation Building ────────────────────────────────────────────

    def _build_relations(
        self, paper: Paper, entities: list[KnowledgeEntity]
    ) -> list[KnowledgeRelation]:
        """Build knowledge graph relations between paper and entities."""
        relations = []

        for entity in entities:
            # Paper → Entity (uses/related_to)
            rel_type = {
                "method": "uses_method",
                "dataset": "uses_dataset",
                "topic": "related_to",
            }.get(entity.entity_type, "related_to")

            relation = KnowledgeRelation(
                source_id=paper.paper_id,
                target_id=entity.entity_id,
                relation_type=rel_type,
                weight=entity.confidence,
                source_paper_id=paper.paper_id,
            )
            relations.append(relation)

            self.kg.add_edge(
                paper.paper_id,
                entity.entity_id,
                rel_type,
                weight=entity.confidence,
            )

        # Add citation edges
        for ref_id in paper.references:
            relation = KnowledgeRelation(
                source_id=paper.paper_id,
                target_id=ref_id,
                relation_type="cites",
                source_paper_id=paper.paper_id,
            )
            relations.append(relation)
            self.kg.add_citation(paper.paper_id, ref_id, year=paper.year or 0)

        # Add authorship edges
        for author in paper.authors:
            author_id = self._make_id("author", author.name)
            self.kg.add_author_node(author_id, author.name)
            self.kg.add_authorship(paper.paper_id, author_id)

        return relations

    # ── Paper Embedding ──────────────────────────────────────────────

    def _embed_paper(self, paper: Paper, text: str) -> None:
        """Chunk and embed paper text in the vector store."""
        try:
            cleaned = clean_text(text)
            chunks = chunk_text(cleaned, chunk_size=512, overlap=50)

            texts = []
            metadatas = []
            ids = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{paper.paper_id}_chunk_{i}"
                texts.append(chunk)
                metadatas.append({
                    "paper_id": paper.paper_id,
                    "title": paper.title,
                    "year": paper.year or 0,
                    "source": paper.source,
                    "chunk_index": i,
                })
                ids.append(chunk_id)

            if texts:
                self.vs.add_documents(texts, metadatas, ids=ids)
                self.logger.debug(f"Embedded {len(texts)} chunks for '{paper.title[:50]}'")

        except Exception as e:
            self.logger.warning(f"Embedding failed for '{paper.title}': {e}")

    # ── Graph Helpers ────────────────────────────────────────────────

    def _add_paper_to_graph(self, paper: Paper) -> None:
        """Add a paper node to the knowledge graph."""
        self.kg.add_paper_node(
            paper.paper_id,
            title=paper.title,
            year=paper.year or 0,
            citation_count=paper.citation_count,
            source=paper.source,
            venue=paper.venue or "",
        )

    @staticmethod
    def _make_id(prefix: str, name: str) -> str:
        """Generate a deterministic ID for an entity."""
        normalized = name.lower().strip()
        hash_suffix = hashlib.md5(normalized.encode()).hexdigest()[:8]
        return f"{prefix}_{hash_suffix}"
