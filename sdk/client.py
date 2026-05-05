"""DevEx Agent SDK — the public interface developers import."""
from dataclasses import dataclass
from agent_platform.agents.orchestrator import Orchestrator, AgentResponse
from agent_platform.llm.nl_parser import parse_query
from agent_platform.memory.semantic import SemanticMemory
from agent_platform.rag.retriever import RAGRetriever


@dataclass
class RecommendationResult:
    """Clean, typed result object returned to SDK consumers."""
    recommendation: str
    confidence: int
    reasoning: str
    tradeoffs: str
    getting_started: str
    alternatives: list[dict]
    avoid: str
    latency_ms: float
    session_id: str


class DevExAgent:
    """
    Main SDK entry point for the DevEx Agent Platform.

    Usage:
        from devex_agent import DevExAgent

        agent = DevExAgent()
        result = agent.recommend("best observability stack for FastAPI")
        print(result.recommendation)
        print(result.reasoning)
    """

    def __init__(self, session_id: str = "default", persist_dir: str = "./chroma_db"):
        self.session_id = session_id
        rag = RAGRetriever(persist_dir=persist_dir)
        semantic_memory = SemanticMemory(persist_dir=persist_dir)
        self.orchestrator = Orchestrator(rag_retriever=rag, semantic_memory=semantic_memory)

    def recommend(self, query: str, stack: list[str] | None = None,
                  constraints: list[str] | None = None) -> RecommendationResult:
        """
        Get a tool recommendation for a developer query.

        Args:
            query: Natural language question (e.g. "best rate limiting library for FastAPI")
            stack: Optional list of technologies in use (e.g. ["FastAPI", "Redis"])
            constraints: Optional constraints (e.g. ["open source only", "small team"])

        Returns:
            RecommendationResult with top pick, reasoning, alternatives, and tradeoffs.
        """
        # Parse NL query into structured context
        parsed = parse_query(query)

        context = {
            "stack": stack or parsed.get("stack", []),
            "constraints": constraints or parsed.get("constraints", []),
            "category": parsed.get("category", "general"),
        }

        response: AgentResponse = self.orchestrator.recommend(
            query=parsed["query"],
            context=context,
            session_id=self.session_id,
        )

        rec = response.ranking.recommendation
        return RecommendationResult(
            recommendation=rec.name,
            confidence=rec.confidence,
            reasoning=rec.reasoning,
            tradeoffs=rec.tradeoffs,
            getting_started=rec.getting_started,
            alternatives=[
                {"name": a.name, "rank": a.rank, "when_to_choose": a.when_to_choose}
                for a in response.ranking.alternatives
            ],
            avoid=response.ranking.avoid,
            latency_ms=response.total_latency_ms,
            session_id=self.session_id,
        )

    def history(self) -> list[dict]:
        """Return session interaction history."""
        return self.orchestrator.episodic.get_context(self.session_id)

    def recall(self, query: str) -> str:
        """Search long-term semantic memory for past decisions."""
        if self.orchestrator.semantic_memory:
            return self.orchestrator.semantic_memory.recall_as_context(query)
        return "Semantic memory not available."
