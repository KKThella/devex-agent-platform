"""Orchestrator — coordinates RetrievalAgent → RankingAgent pipeline."""
import time
from dataclasses import dataclass, field
from agent_platform.agents.retrieval_agent import RetrievalAgent, RetrievalResult
from agent_platform.agents.ranking_agent import RankingAgent, RankingResult
from agent_platform.memory.episodic import EpisodicMemory
from agent_platform.observability.metrics import MetricsCollector


@dataclass
class AgentResponse:
    retrieval: RetrievalResult
    ranking: RankingResult
    session_id: str
    total_latency_ms: float
    memory_context_used: bool = False


class Orchestrator:
    """
    Coordinates the two-agent pipeline:
      1. EpisodicMemory enriches query with session context
      2. RetrievalAgent finds candidates (RAG + LLM)
      3. RankingAgent produces final recommendation
      4. Result logged to metrics + memory
    """

    def __init__(self, rag_retriever=None, semantic_memory=None):
        self.retrieval_agent = RetrievalAgent(rag_retriever=rag_retriever)
        self.ranking_agent = RankingAgent()
        self.episodic = EpisodicMemory()
        self.semantic_memory = semantic_memory
        self.metrics = MetricsCollector()

    def recommend(self, query: str, context: dict | None = None, session_id: str = "default") -> AgentResponse:
        """Run the full agent pipeline for a developer query."""
        context = context or {}
        start = time.perf_counter()

        # 1. Enrich context with episodic memory
        memory_ctx = self.episodic.get_context(session_id)
        memory_context_used = bool(memory_ctx)
        if memory_ctx:
            context["session_history"] = memory_ctx

        # 2. RetrievalAgent
        retrieval = self.retrieval_agent.run(query, context)

        # 3. RankingAgent
        ranking = self.ranking_agent.run(retrieval, context)

        total_ms = (time.perf_counter() - start) * 1000

        # 4. Log to episodic memory
        self.episodic.add(session_id, {
            "query": query,
            "recommendation": ranking.recommendation.name,
            "confidence": ranking.recommendation.confidence,
        })

        # 5. Persist to semantic memory if available
        if self.semantic_memory:
            self.semantic_memory.store(
                text=f"Query: {query} → Recommended: {ranking.recommendation.name}. {ranking.recommendation.reasoning}",
                metadata={"session_id": session_id, "confidence": ranking.recommendation.confidence}
            )

        # 6. Emit metrics
        self.metrics.record(
            query=query,
            latency_ms=total_ms,
            retrieval_latency_ms=retrieval.latency_ms,
            ranking_latency_ms=ranking.latency_ms,
            confidence=ranking.recommendation.confidence,
            session_id=session_id,
        )

        return AgentResponse(
            retrieval=retrieval,
            ranking=ranking,
            session_id=session_id,
            total_latency_ms=total_ms,
            memory_context_used=memory_context_used,
        )
