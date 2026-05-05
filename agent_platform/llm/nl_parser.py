"""Natural language query parser — extracts structured intent from plain English."""
import json
from dataclasses import dataclass, field
from typing import List, Optional
from agent_platform.llm.client import call_claude
from agent_platform.llm.prompts import NL_PARSER_SYSTEM


@dataclass
class ParsedQuery:
    """Structured output from the NL parser."""
    query: str
    stack: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    category: str = "general"
    urgency: str = "exploratory"
    team_size: Optional[str] = None


class NLParser:
    """Wraps parse_query as a class for use in the Streamlit app and SDK."""

    def parse(self, raw_query: str) -> ParsedQuery:
        result = parse_query(raw_query)
        return ParsedQuery(
            query=result.get("query", raw_query),
            stack=result.get("stack", []),
            constraints=result.get("constraints", []),
            category=result.get("category", "general"),
            urgency=result.get("urgency", "exploratory"),
            team_size=result.get("team_size", None),
        )


def parse_query(raw_query: str) -> dict:
    """
    Turn a plain-English developer question into structured context
    that the agent pipeline can act on.

    Example:
      "best rate limiting lib for FastAPI with Redis, small team"
      → {"query": "rate limiting library", "stack": ["FastAPI", "Redis"],
         "constraints": ["small team"], "category": "infra", "urgency": "evaluating"}
    """
    raw, _ = call_claude(NL_PARSER_SYSTEM, f'Query: "{raw_query}"', max_tokens=300)
    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # Graceful fallback — return raw query unmodified
        return {
            "query": raw_query,
            "stack": [],
            "constraints": [],
            "category": "general",
            "urgency": "exploratory",
        }
