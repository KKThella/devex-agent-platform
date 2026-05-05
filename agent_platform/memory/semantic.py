"""Semantic memory — long-term, persistent, vector-backed memory."""
import os
import uuid
import tempfile
import chromadb
from typing import Optional, Dict, List
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from datetime import datetime


MEMORY_COLLECTION = "agent_semantic_memory"


class SemanticMemory:
    """
    Persists recommendations, decisions, and outcomes across sessions.
    Backed by ChromaDB — survives process restarts.
    Enables the agent to say 'your team previously chose X for similar reasons.'
    """

    def __init__(self, persist_dir: str = None):
        # Use tempfile on Streamlit Cloud, allow override for local testing
        if persist_dir is None:
            persist_dir = os.path.join(tempfile.gettempdir(), "chroma_db")
        
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=MEMORY_COLLECTION,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

    def store(self, text: str, metadata: Optional[Dict] = None):
        """Persist a recommendation or decision to long-term memory."""
        metadata = metadata or {}
        metadata["stored_at"] = datetime.utcnow().isoformat()
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())],
        )

    def recall(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve semantically similar past decisions."""
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
        )
        memories = []
        for i, doc in enumerate(results["documents"][0]):
            memories.append({
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i],
            })
        return memories

    def recall_as_context(self, query: str) -> str:
        """Return past decisions as a formatted string for agent context injection."""
        memories = self.recall(query, top_k=3)
        if not memories:
            return ""
        lines = ["Relevant past decisions from team memory:"]
        for m in memories:
            lines.append(f"  - {m['text']} (similarity: {m['similarity']:.2f})")
        return "\n".join(lines)

    @property
    def count(self) -> int:
        return self.collection.count()
