"""Natural language query parser — extracts structured intent from plain English."""
import json
from agent_platform.llm.client import call_claude
from agent_platform.llm.prompts import NL_PARSER_SYSTEM


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
