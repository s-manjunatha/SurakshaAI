"""RAG pipeline using ChromaDB and PostgreSQL."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Optional
from app.config import get_settings

settings = get_settings()


class RAGService:
    def __init__(self):
        self._encoder = None
        self._client = None
        self._collection = None

    @property
    def encoder(self):
        if self._encoder is None:
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
        return self._encoder

    def _get_client(self):
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def embed_text(self, text: str) -> List[float]:
        return self.encoder.encode(text).tolist()

    def add_fir_document(self, fir_id: str, fir_number: str, text: str, metadata: dict):
        collection = self._get_collection()
        embedding = self.embed_text(text)
        collection.upsert(
            ids=[fir_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"fir_number": fir_number, **metadata}],
        )

    def search_similar(self, query: str, n_results: int = 10, filter_dict: Optional[dict] = None) -> List[dict]:
        collection = self._get_collection()
        query_embedding = self.embed_text(query)
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if filter_dict:
            kwargs["where"] = filter_dict

        try:
            results = collection.query(**kwargs)
        except Exception:
            return []

        similar = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = max(0, 1 - distance)
                similar.append({
                    "fir_id": doc_id,
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "similarity_score": round(similarity, 4),
                })
        return similar

    def build_fir_text(self, fir: dict) -> str:
        parts = [
            f"FIR {fir.get('fir_number', '')}",
            f"Crime: {fir.get('crime_type', '')}",
            f"Title: {fir.get('title', '')}",
            f"Description: {fir.get('description', '')}",
            f"District: {fir.get('district', '')}",
            f"Status: {fir.get('status', '')}",
        ]
        if fir.get("summary"):
            parts.append(f"Summary: {fir['summary']}")
        if fir.get("ipc_sections"):
            parts.append(f"IPC: {', '.join(fir['ipc_sections'])}")
        return " | ".join(parts)


rag_service = RAGService()
