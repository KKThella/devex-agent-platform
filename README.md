# DevEx Agent Platform

> An AI-powered developer experience platform that uses multi-agent architecture, retrieval-augmented generation, and persistent memory to recommend the right tools, libraries, and workflows — in plain English.

[![CI](https://github.com/KKThella/devex-agent-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/KKThella/devex-agent-platform/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

Developer teams waste hours every sprint evaluating tools, debugging dependency conflicts, and rediscovering patterns already solved by others on the team. Existing solutions are either too generic (Stack Overflow) or too narrow (internal wikis no one updates). There is no intelligent, context-aware layer that understands *your* stack, *your* team's history, and *your* current project goals.

## What This Builds

DevEx Agent Platform is a developer-facing SDK and CLI that gives teams an agentic recommendation layer on top of their existing workflows. It answers questions like:

- *"What's the best rate-limiting library for a FastAPI service with Redis?"*
- *"We're migrating from REST to gRPC — what should we watch out for?"*
- *"What tools does our team already use for observability?"*

Unlike a chatbot, it **remembers** your context across sessions, **retrieves** from a curated knowledge base of real engineering decisions, and uses **two coordinated agents** to separate retrieval from reasoning — improving both accuracy and explainability.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Developer Interface                │
│         CLI (devex recommend)  │  Python SDK         │
│         Natural Language Query │  REST API           │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │   Orchestrator Layer  │
         │  (Agent Coordinator)  │
         └───────┬───────┬───────┘
                 │       │
    ┌────────────▼─┐  ┌──▼──────────────┐
    │  Retrieval   │  │  Ranking &       │
    │  Agent       │  │  Reasoning Agent │
    │              │  │                  │
    │ ChromaDB RAG │  │ Claude claude-   │
    │ Semantic     │  │ sonnet-4-6       │
    │ Search       │  │ Re-ranking +     │
    │              │  │ Explanation      │
    └──────┬───────┘  └──────┬──────────┘
           │                  │
    ┌──────▼──────────────────▼──────┐
    │         Memory Layer           │
    │  Episodic (session context)    │
    │  Semantic (ChromaDB vectors)   │
    └────────────────────────────────┘
           │
    ┌──────▼──────────────────────────┐
    │      Knowledge Base             │
    │  Dev tools · Patterns · Docs    │
    │  Team decisions · ADRs          │
    └─────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Multi-agent over single LLM | RetrievalAgent + RankingAgent | Separation of concerns: retrieval optimizes for recall, ranking optimizes for precision + explainability |
| Vector DB | ChromaDB (local) / Pinecone (prod) | Local-first for dev speed; swap to hosted for scale with zero code change |
| Memory model | Episodic + Semantic | Episodic captures session context (what we discussed); Semantic persists decisions across sessions |
| LLM | Claude claude-sonnet-4-6 | Best-in-class reasoning for nuanced engineering tradeoffs |
| SDK-first | Python package + CLI | Developers adopt tools through their existing workflow, not new UIs |

---

## Quickstart

### Install

```bash
pip install devex-agent-platform
```

### Configure

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY
```

### Use the CLI

```bash
# Get tool recommendations in natural language
devex recommend "best observability stack for a Python microservice"

# Ask with context about your current stack
devex recommend "rate limiting library" --stack "FastAPI, Redis, PostgreSQL"

# See what the team has used before (memory)
devex history --last 10
```

### Use the SDK

```python
from devex_agent import DevExAgent

agent = DevExAgent()

# Natural language recommendation
result = agent.recommend(
    query="best testing framework for async Python APIs",
    context={"stack": ["FastAPI", "PostgreSQL"], "team_size": 8}
)

print(result.recommendation)   # Top pick with reasoning
print(result.alternatives)     # Ranked alternatives
print(result.tradeoffs)        # What you're giving up
print(result.confidence)       # 0-100 confidence score
```

---

## Features

### Multi-Agent Orchestration
Two specialized agents collaborate on every query: a **RetrievalAgent** that performs semantic search over the knowledge base, and a **RankingAgent** that re-ranks results using LLM reasoning about your specific constraints.

### RAG Pipeline
Recommendations are grounded in a curated knowledge base of 500+ developer tools, patterns, and architecture decision records — not just LLM training data. ChromaDB provides sub-100ms semantic retrieval.

### Agent Memory
- **Episodic memory**: Remembers everything discussed in the current session
- **Semantic memory**: Persists team decisions, past recommendations, and feedback across sessions — so it gets smarter over time

### Natural Language Interface
Ask questions the way you'd ask a senior engineer. No query syntax, no filters — just plain English.

### Observability
Every recommendation is logged with latency, confidence score, retrieval hit rate, and user feedback signal. Metrics are exposed via `/metrics` endpoint compatible with Prometheus.

### Developer SDK + CLI
First-class Python SDK with type hints and async support. CLI built on Typer for shell integration.

---

## Observability & Metrics

| Metric | Description | Target SLO |
|---|---|---|
| `recommendation_latency_p99` | End-to-end response time | < 3s |
| `retrieval_hit_rate` | % of queries with relevant RAG results | > 85% |
| `agent_confidence_avg` | Average confidence score | > 72 |
| `error_rate` | Failed requests / total requests | < 1% |

Access the metrics dashboard:
```bash
devex metrics --dashboard   # Opens Streamlit dashboard
devex metrics --export      # Exports JSON for Prometheus
```

---

## CI/CD Pipeline

```
push → [lint + typecheck] → [unit tests] → [integration tests] → [build] → [deploy staging] → [smoke test] → [deploy prod]
```

DORA metrics are tracked on every deploy:
- **Deployment Frequency**: Tracked per release tag
- **Lead Time**: PR open → production deploy time
- **MTTR**: Rollback time tracked via GitHub Actions job duration
- **Change Failure Rate**: Failed deploys / total deploys

---

## Project Roadmap

| Status | Feature |
|---|---|
| ✅ | Core rec engine |
| ✅ | RAG pipeline + ChromaDB |
| ✅ | Multi-agent orchestration |
| ✅ | Agent memory (episodic + semantic) |
| ✅ | Natural language interface |
| ✅ | Python SDK + CLI |
| ✅ | Observability dashboard |
| ✅ | GitHub Actions CI/CD |
| 🔜 | Team knowledge base ingestion (Confluence, Notion, ADRs) |
| 🔜 | Slack bot integration |
| 🔜 | VS Code extension |

---

## Why I Built This

I'm a Staff/Principal Product Manager with 13+ years building AI-powered platforms at Nike. This project is a hands-on prototype to close the gap between PM strategy and engineering execution — specifically around agentic systems, developer tooling, and platform thinking.

The patterns here — multi-agent orchestration, RAG-grounded recommendations, persistent memory, developer-first SDK design — directly mirror the architecture decisions I drive in production systems at scale.

**Related work:** [Nike LLM Order Management Agent](#) · [AI Personalization Platform ($115M ARR)](#) · [iHerb Recs Demo](https://github.com/KKThella/Recs_Demo)

---

## Contributing

```bash
git clone https://github.com/KKThella/devex-agent-platform
cd devex-agent-platform
pip install -e ".[dev]"
pytest tests/
```

---

*Built by [Kiran Thella](https://linkedin.com/in/kiran-thella) · [LinkedIn](https://linkedin.com/in/kiran-thella)*
