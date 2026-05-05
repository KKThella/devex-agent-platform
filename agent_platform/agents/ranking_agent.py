"""RankingAgent — re-ranks candidates and produces final recommendation."""
import json
from typing import List, Optional, Dict
from dataclasses import dataclass
from agent_platform.llm.client import call_claude
from agent_platform.llm.prompts import RANKING_AGENT_SYSTEM
from agent_platform.agents.retrieval_agent import RetrievalResult


@dataclass
class Recommendation:
    name: str
    confidence: int
    reasoning: str
    tradeoffs: str
    getting_started: str


@dataclass
class Alternative:
    name: str
    rank: int
    when_to_choose: str


@dataclass
class RankingResult:
    recommendation: Recommendation
    alternatives: List[Alternative]
    avoid: str
    latency_ms: float


class RankingAgent:
    """
    Agent 2 of 2: Re-ranks RetrievalAgent candidates using deep reasoning.
    Produces a final recommendation with tradeoffs and alternatives.
    """

    def run(self, retrieval: RetrievalResult, context: Optional[Dict] = None) -> RankingResult:
        """Rank candidates and return best recommendation."""
        context = context or {}

        candidates_summary = "\n".join(
            f"{i+1}. {c.name} (relevance: {c.relevance_score}/100) — {c.why_relevant}"
            for i, c in enumerate(retrieval.candidates)
        )

        user_msg = f"""Developer intent: "{retrieval.query_intent}"
Stack: {json.dumps(context.get('stack', []))}
Constraints: {json.dumps(context.get('constraints', []))}

Candidate tools retrieved:
{candidates_summary}

Analyze these candidates and return your ranked recommendation as JSON."""

        raw, latency = call_claude(RANKING_AGENT_SYSTEM, user_msg, max_tokens=900)
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)

        rec_data = parsed["recommendation"]
        recommendation = Recommendation(
            name=rec_data["name"],
            confidence=rec_data["confidence"],
            reasoning=rec_data["reasoning"],
            tradeoffs=rec_data["tradeoffs"],
            getting_started=rec_data["getting_started"],
        )
        alternatives = [Alternative(**a) for a in parsed.get("alternatives", [])]

        return RankingResult(
            recommendation=recommendation,
            alternatives=alternatives,
            avoid=parsed.get("avoid", ""),
            latency_ms=latency,
        )
