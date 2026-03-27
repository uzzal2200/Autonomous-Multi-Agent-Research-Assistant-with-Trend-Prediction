"""
ResearchAI - Vector Store Manager
ChromaDB-based vector store for paper embeddings and semantic search.
Uses free sentence-transformers (all-MiniLM-L6-v2) for embeddings.
"""

from pathlib import Path
from typing import Optional
import hashlib

from src.utils.logger import get_logger
from config.settings import model_settings, storage_settings

logger = get_logger("vector_store")


class VectorStoreManager:
    """Manages ChromaDB collections for paper embeddings and RAG.

    Embeds paper text chunks using sentence-transformers (free, local).
    Supports semantic similarity search for downstream agents.
    """

    def __init__(self):
        self._persist_dir = storage_settings.chroma_persist_dir
        self._embedding_model_name = model_settings.embedding_model
        self._client = None
        self._embedding_fn = None

    def _ensure_initialized(self):
        """Lazy-initialize ChromaDB client and embedding function."""
        if self._client is not None:
            return

        import chromadb
        from chromadb.utils import embedding_functions

        Path(self._persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self._embedding_model_name,
        )
        logger.info(f"ChromaDB initialized at {self._persist_dir} with {self._embedding_model_name}")

    def get_or_create_collection(self, collection_name: str = "papers"):
        """Get or create a ChromaDB collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            ChromaDB collection object.
        """
        self._ensure_initialized()
        return self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict],
        collection_name: str = "papers",
        ids: Optional[list[str]] = None,
    ) -> None:
        """Add text documents to the vector store.

        Args:
            texts: List of text chunks to embed and store.
            metadatas: Corresponding metadata dicts for each chunk.
            collection_name: Target collection name.
            ids: Optional custom IDs. Auto-generated if not provided.
        """
        collection = self.get_or_create_collection(collection_name)

        if ids is None:
            ids = [
                hashlib.md5(text.encode()).hexdigest()[:16]
                for text in texts
            ]

        # ChromaDB handles batching internally
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Added {len(texts)} documents to collection '{collection_name}'")

    def search(
        self,
        query: str,
        n_results: int = 10,
        collection_name: str = "papers",
        where: Optional[dict] = None,
    ) -> list[dict]:
        """Semantic similarity search.

        Args:
            query: Natural language query.
            n_results: Number of results to return.
            collection_name: Collection to search.
            where: Optional metadata filter (ChromaDB where clause).

        Returns:
            List of result dicts with 'text', 'metadata', 'distance'.
        """
        collection = self.get_or_create_collection(collection_name)
        count = collection.count()
        if count == 0:
            logger.debug("Collection is empty, returning no results")
            return []

        kwargs = {
            "query_texts": [query],
            "n_results": min(n_results, count),
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
            })

        logger.debug(f"Search '{query[:50]}...' returned {len(output)} results")
        return output

    def get_collection_stats(self, collection_name: str = "papers") -> dict:
        """Get statistics for a collection."""
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection_name,
            "count": collection.count(),
        }

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        self._ensure_initialized()
        try:
            self._client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
        except Exception as e:
            logger.warning(f"Failed to delete collection '{collection_name}': {e}")
