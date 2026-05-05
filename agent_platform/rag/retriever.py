"""RAG Retriever — ChromaDB-backed semantic search over developer knowledge base."""
import os
import tempfile
import chromadb
from typing import Optional, List, Dict
from chromadb.utils import embedding_functions
from agent_platform.rag.knowledge_base import KNOWLEDGE_BASE


COLLECTION_NAME = "devex_knowledge"


class RAGRetriever:
    """
    Semantic retrieval over the developer tools knowledge base.
    Uses ChromaDB with sentence-transformers embeddings (local, no API key needed).
    Swap to Pinecone for production scale.
    """

    def __init__(self, persist_dir: str = None):
        # Use tempfile on Streamlit Cloud, allow override for local testing
        if persist_dir is None:
            persist_dir = os.path.join(tempfile.gettempdir(), "chroma_db")
        
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._seed_if_empty()

    def _seed_if_empty(self):
        """Seed the knowledge base on first run."""
        if self.collection.count() == 0:
            print("Seeding knowledge base...")
            self.collection.add(
                documents=[doc["text"] for doc in KNOWLEDGE_BASE],
                metadatas=[{"category": doc["category"], "tool": doc["tool"]} for doc in KNOWLEDGE_BASE],
                ids=[f"doc_{i}" for i in range(len(KNOWLEDGE_BASE))],
            )
            print(f"Seeded {len(KNOWLEDGE_BASE)} documents.")

    def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict]:
        """Return top_k most relevant knowledge base entries for query."""
        where = {"category": category} if category else None
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
            where=where,
        )
        docs = []
        for i, doc in enumerate(results["documents"][0]):
            docs.append({
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return docs

    def add_document(self, text: str, metadata: Dict, doc_id: Optional[str] = None):
        """Add a new document to the knowledge base (team decision, ADR, etc)."""
        import uuid
        doc_id = doc_id or str(uuid.uuid4())
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id],
        )
        return doc_id

    @property
    def count(self) -> int:
        return self.collection.count()
