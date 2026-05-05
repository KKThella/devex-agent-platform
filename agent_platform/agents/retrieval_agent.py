"""RetrievalAgent — finds candidate tools via RAG + LLM."""
import json
from dataclasses import dataclass
from agent_platform.llm.client import call_claude
from agent_platform.llm.prompts import RETRIEVAL_AGENT_SYSTEM


@dataclass
class Candidate:
    name: str
    category: str
    relevance_score: int
    why_relevant: str
    source: str


@dataclass
class RetrievalResult:
    candidates: list[Candidate]
    query_intent: str
    latency_ms: float


class RetrievalAgent:
    """
    Agent 1 of 2: Retrieves candidate tools for a developer query.
    Uses RAG-grounded search first, falls back to LLM knowledge.
    """

    def __init__(self, rag_retriever=None):
        self.rag = rag_retriever  # injected — None = LLM-only mode

    def run(self, query: str, context: dict | None = None) -> RetrievalResult:
        """Retrieve candidates for a developer query."""
        context = context or {}

        # Build RAG context if available
        rag_context = ""
        if self.rag:
            rag_docs = self.rag.search(query, top_k=5)
            if rag_docs:
                rag_context = "\n\nKnowledge base context:\n" + "\n".join(
                    f"- {doc['text']}" for doc in rag_docs
                )

        user_msg = f"""Developer query: "{query}"
Stack context: {json.dumps(context.get('stack', []))}
Constraints: {json.dumps(context.get('constraints', []))}
Team size: {context.get('team_size', 'unknown')}{rag_context}

Return 6 candidate tools as JSON."""

        raw, latency = call_claude(RETRIEVAL_AGENT_SYSTEM, user_msg, max_tokens=800)

        # Parse JSON — strip markdown fences if present
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)

        candidates = [Candidate(**c) for c in parsed["candidates"]]
        return RetrievalResult(
            candidates=candidates,
            query_intent=parsed["query_intent"],
            latency_ms=latency,
        )
