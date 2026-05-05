"""Anthropic API client — thin wrapper used by all agents."""
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def call_claude(system: str, user: str, max_tokens: int = 1024) -> tuple[str, float]:
    """Call Claude and return (content, latency_ms)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }

    start = time.perf_counter()
    with httpx.Client(timeout=30) as client:
        response = client.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
    latency_ms = (time.perf_counter() - start) * 1000

    return response.json()["content"][0]["text"], latency_ms
