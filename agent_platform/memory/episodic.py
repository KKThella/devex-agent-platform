"""Episodic memory — short-term, session-scoped context."""
from collections import defaultdict
from typing import Dict, List, Optional
from datetime import datetime


class EpisodicMemory:
    """
    Stores per-session interaction history in memory.
    Gives agents awareness of what was discussed earlier in the same session.
    Resets when the process restarts (use SemanticMemory for persistence).
    """

    def __init__(self, max_turns: int = 20):
        self._store: Dict[str, List[Dict]] = defaultdict(list)
        self.max_turns = max_turns

    def add(self, session_id: str, entry: Dict):
        """Record an interaction turn."""
        entry["timestamp"] = datetime.utcnow().isoformat()
        self._store[session_id].append(entry)
        # Keep only last N turns
        if len(self._store[session_id]) > self.max_turns:
            self._store[session_id] = self._store[session_id][-self.max_turns:]

    def get_context(self, session_id: str) -> List[Dict]:
        """Return recent interaction history for a session."""
        return self._store.get(session_id, [])

    def get_last_recommendation(self, session_id: str) -> Optional[str]:
        """Shortcut: what did we last recommend in this session?"""
        history = self._store.get(session_id, [])
        if history:
            return history[-1].get("recommendation")
        return None

    def clear(self, session_id: str):
        """Reset a session's memory."""
        self._store.pop(session_id, None)

    def summary(self, session_id: str) -> str:
        """Human-readable session summary for debugging."""
        history = self._store.get(session_id, [])
        if not history:
            return "No history for this session."
        lines = [f"Session {session_id} — {len(history)} turns:"]
        for i, turn in enumerate(history):
            lines.append(f"  {i+1}. Q: {turn.get('query','?')} → {turn.get('recommendation','?')} ({turn.get('confidence','?')}% confidence)")
        return "\n".join(lines)
