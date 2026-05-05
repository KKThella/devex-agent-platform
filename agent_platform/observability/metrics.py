"""Metrics collector — tracks latency, confidence, errors, and DORA signals."""
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


METRICS_FILE = Path("./metrics_store.json")


class MetricsCollector:
    """
    Lightweight observability layer for the agent platform.
    Tracks: latency, confidence, retrieval hit rate, error rate.
    Exposes Prometheus-compatible /metrics output.
    DORA metrics tracked via deployment events.
    """

    def __init__(self):
        self._requests: list[dict] = []
        self._errors: list[dict] = []
        self._deployments: list[dict] = []
        self._load_persisted()

    def record(self, query: str, latency_ms: float, retrieval_latency_ms: float,
               ranking_latency_ms: float, confidence: int, session_id: str):
        """Record a successful recommendation request."""
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "query": query[:100],
            "latency_ms": round(latency_ms, 1),
            "retrieval_latency_ms": round(retrieval_latency_ms, 1),
            "ranking_latency_ms": round(ranking_latency_ms, 1),
            "confidence": confidence,
            "session_id": session_id,
        }
        self._requests.append(entry)
        self._persist()

    def record_error(self, query: str, error: str, session_id: str):
        """Record a failed request."""
        self._errors.append({
            "ts": datetime.utcnow().isoformat(),
            "query": query[:100],
            "error": str(error)[:200],
            "session_id": session_id,
        })
        self._persist()

    def record_deployment(self, version: str, environment: str, success: bool, duration_s: float):
        """Record a deployment event for DORA metrics."""
        self._deployments.append({
            "ts": datetime.utcnow().isoformat(),
            "version": version,
            "environment": environment,
            "success": success,
            "duration_s": duration_s,
        })
        self._persist()

    def summary(self) -> dict:
        """Compute current metrics summary."""
        total = len(self._requests)
        errors = len(self._errors)

        if total == 0:
            return {"status": "no data"}

        latencies = [r["latency_ms"] for r in self._requests]
        confidences = [r["confidence"] for r in self._requests]
        latencies_sorted = sorted(latencies)

        def percentile(data, p):
            if not data: return 0
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data)-1)]

        # DORA metrics
        deploys = self._deployments
        deploy_freq = len([d for d in deploys if d["success"]]) / max(1, (datetime.utcnow() - datetime(2024,1,1)).days / 7)
        change_failure_rate = len([d for d in deploys if not d["success"]]) / max(1, len(deploys))

        return {
            "request_count": total,
            "error_count": errors,
            "error_rate_pct": round(errors / (total + errors) * 100, 2),
            "latency_p50_ms": percentile(latencies_sorted, 50),
            "latency_p95_ms": percentile(latencies_sorted, 95),
            "latency_p99_ms": percentile(latencies_sorted, 99),
            "confidence_avg": round(sum(confidences) / total, 1),
            "dora": {
                "deployment_count": len(deploys),
                "deploy_frequency_per_week": round(deploy_freq, 2),
                "change_failure_rate_pct": round(change_failure_rate * 100, 1),
            }
        }

    def prometheus_export(self) -> str:
        """Export metrics in Prometheus text format."""
        s = self.summary()
        if "status" in s:
            return "# No data\n"
        lines = [
            f"# HELP devex_request_total Total recommendation requests",
            f"devex_request_total {s['request_count']}",
            f"# HELP devex_error_total Total failed requests",
            f"devex_error_total {s['error_count']}",
            f"# HELP devex_latency_p99_ms 99th percentile latency",
            f"devex_latency_p99_ms {s['latency_p99_ms']}",
            f"# HELP devex_confidence_avg Average recommendation confidence",
            f"devex_confidence_avg {s['confidence_avg']}",
            f"# HELP devex_change_failure_rate DORA change failure rate",
            f"devex_change_failure_rate {s['dora']['change_failure_rate_pct']}",
        ]
        return "\n".join(lines) + "\n"

    def _persist(self):
        try:
            METRICS_FILE.write_text(json.dumps({
                "requests": self._requests[-1000:],
                "errors": self._errors[-200:],
                "deployments": self._deployments,
            }, indent=2))
        except Exception:
            pass

    def _load_persisted(self):
        if METRICS_FILE.exists():
            try:
                data = json.loads(METRICS_FILE.read_text())
                self._requests = data.get("requests", [])
                self._errors = data.get("errors", [])
                self._deployments = data.get("deployments", [])
            except Exception:
                pass
