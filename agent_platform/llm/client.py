"""Anthropic API client — thin wrapper used by all agents."""
import os
import time
import httpx
import streamlit as st
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def get_api_key() -> str:
    """Get API key from Streamlit secrets (Cloud) or environment (local)."""
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")


def call_claude(system: str, user: str, max_tokens: int = 1024) -> Tuple[str, float]:
    """Call Claude and return (content, latency_ms)."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment or Streamlit secrets")

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
