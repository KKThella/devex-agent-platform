# DevEx Agent Platform

> An AI-powered developer experience platform that uses multi-agent architecture, retrieval-augmented generation, and persistent memory to recommend the right developer tools — in plain English.

<div align="center">

[![🚀 Live Demo](https://img.shields.io/badge/🚀_Live_Demo-devex--agent--platform-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://devex-agent-platform-txn.streamlit.app)
[![CI](https://github.com/KKThella/devex-agent-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/KKThella/devex-agent-platform/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Try the live demo →](https://devex-agent-platform-txn.streamlit.app)**

</div>

---

## Demo

> Ask anything in plain English — watch the multi-agent pipeline reason through it in real time.

![DevEx Agent Platform — Landing](https://devex-agent-platform-txn.streamlit.app)

| What you see | What's happening under the hood |
|---|---|
| **Step 1 — NL Parser** | Extracts structured intent (stack, constraints, category) from your plain-English query |
| **Step 2 — Retrieval Agent** | Semantic search across 25 curated dev tool entries + LLM-grounded candidate generation |
| **Step 3 — Ranking Agent** | Claude re-ranks candidates against your specific stack and constraints, with full reasoning |
| **Recommendation card** | Winner with confidence score, tradeoffs, alternatives, and getting-started command |

**[→ Try it live](https://devex-agent-platform-txn.streamlit.app)**

---

## The Problem

Developer teams waste hours every sprint evaluating tools, debugging dependency conflicts, and rediscovering patterns already solved by others on the team. Existing solutions are either too generic (Stack Overflow) or too narrow (internal wikis no one updates). There is no intelligent, context-aware layer that understands *your* stack, *your* team's history, and *your* current project goals.

## What This Builds

DevEx Agent Platform is a developer-facing SDK, CLI, and interactive web app that gives teams an agentic recommendation layer on top of their existing workflows. It answers questions like:

- *"What's the best rate-limiting library for a FastAPI service with Redis?"*
- *"We're migrating from REST to gRPC — what should we watch out for?"*
- *"What tools does our team already use for observability?"*

Unlike a chatbot, it **remembers** your context across sessions, **retrieves** from a curated knowledge base of real engineering decisions, and uses **two coordinated agents** to separate retrieval from reasoning — improving both accuracy and explainability.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Interfaces                      │
│   Streamlit Web UI  │  CLI (devex recommend)  │  Python SDK  │
│   Natural Language Query  │  REST API                        │
└─────────────────────────┬───────────────────────────────────┘
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
         │ ChromaDB RAG │  │ Claude Sonnet    │
         │ Semantic     │  │ Re-ranking +     │
         │ Search       │  │ Explanation      │
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
         │  25 curated dev tools           │
         │  Observability · Testing        │
         │  Infra · Security · Agent/LLM   │
         └─────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Multi-agent over single LLM | RetrievalAgent + RankingAgent | Separation of concerns: retrieval optimizes for recall, ranking optimizes for precision + explainability |
| Vector DB | ChromaDB (local) / Pinecone (prod) | Local-first for dev speed; swap to hosted for scale with zero code change |
| Memory model | Episodic + Semantic | Episodic captures session context (what we discussed); Semantic persists decisions across sessions |
| LLM | Claude claude-sonnet-4-6 | Best-in-class reasoning for nuanced engineering tradeoffs |
| SDK-first | Python package + CLI + Web UI | Developers adopt tools through their existing workflow; PMs demo through the web UI |

---

## Quickstart

### Option 1 — Live Web Demo (no setup)

**[→ devex-agent-platform-txn.streamlit.app](https://devex-agent-platform-txn.streamlit.app)**

Click any example query or type your own. Watch the 3-step pipeline run in real time.

### Option 2 — Run locally

```bash
git clone https://github.com/KKThella/devex-agent-platform
cd devex-agent-platform

python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install streamlit chromadb sentence-transformers

cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

streamlit run app.py
```

### Option 3 — CLI

```bash
# Get tool recommendations in natural language
devex recommend "best observability stack for a Python microservice"

# Ask with context about your current stack
devex recommend "rate limiting library" --stack "FastAPI, Redis, PostgreSQL"

# See what the team has used before (memory)
devex history --last 10
```

### Option 4 — Python SDK

```python
from sdk.client import DevExAgent

agent = DevExAgent()

result = agent.recommend(
    query="best testing framework for async Python APIs",
    stack=["FastAPI", "PostgreSQL"],
    constraints=["open source"]
)

print(result.recommendation)   # Top pick with reasoning
print(result.alternatives)     # Ranked alternatives
print(result.confidence)       # 0-100 confidence score
```

---

## Features

### 🤖 Multi-Agent Orchestration
Two specialized agents collaborate on every query: a **RetrievalAgent** that performs semantic search over the knowledge base, and a **RankingAgent** that re-ranks results using Claude's reasoning about your specific constraints. The Orchestrator coordinates them and logs every interaction.

### 🔍 RAG Pipeline
Recommendations are grounded in a curated knowledge base of 25 developer tools across 7 categories (observability, testing, infra, security, database, framework, agent/LLM). ChromaDB provides semantic retrieval — finds relevant tools even when your query doesn't use the exact right words.

### 🧠 Agent Memory
- **Episodic memory**: Remembers everything discussed in the current session — each query enriches the next
- **Semantic memory**: Persists team decisions, past recommendations, and context across sessions via ChromaDB vectors

### 🗣️ Natural Language Interface
Ask questions the way you'd ask a senior engineer. The NL Parser extracts structured intent (stack, constraints, category, urgency) before hitting the agents.

### 📊 Observability & DORA Metrics
Every recommendation logged with latency, confidence score, retrieval hit rate. DORA metrics (lead time, deploy frequency, change failure rate) tracked in CI. Prometheus-compatible `/metrics` export.

### 🧪 Tested & CI/CD
10 unit tests across agents, memory, and RAG. LLM calls mocked — CI runs fast and free. GitHub Actions pipeline: lint → type-check → tests → DORA tracking.

---

## Project Structure

```
devex-agent-platform/
├── app.py                          # Streamlit web UI
├── agent_platform/
│   ├── agents/
│   │   ├── orchestrator.py         # Coordinates the pipeline
│   │   ├── retrieval_agent.py      # Agent 1: finds candidates
│   │   └── ranking_agent.py        # Agent 2: picks the winner
│   ├── llm/
│   │   ├── client.py               # Claude API wrapper
│   │   ├── nl_parser.py            # NL → structured intent
│   │   └── prompts.py              # System prompts for each agent
│   ├── memory/
│   │   ├── episodic.py             # Session-scoped memory
│   │   └── semantic.py             # Persistent ChromaDB memory
│   ├── rag/
│   │   ├── knowledge_base.py       # 25 curated dev tool entries
│   │   └── retriever.py            # ChromaDB semantic search
│   └── observability/
│       └── metrics.py              # Latency, confidence, DORA metrics
├── sdk/client.py                   # Python SDK for developers
├── cli/main.py                     # Typer CLI
├── tests/                          # 10 unit tests (mocked LLM)
└── .github/workflows/ci.yml        # Lint → test → DORA tracking
```

---

## Observability & Metrics

| Metric | Description | Target SLO |
|---|---|---|
| `recommendation_latency_p99` | End-to-end response time | < 3s |
| `retrieval_hit_rate` | % of queries with relevant RAG results | > 85% |
| `agent_confidence_avg` | Average confidence score | > 72 |
| `error_rate` | Failed requests / total requests | < 1% |

DORA metrics tracked on every merge to main via GitHub Actions:
- **Lead Time**: PR open → main merge time
- **Deploy Frequency**: Tracked per release
- **Change Failure Rate**: Failed deploys / total deploys

---

## CI/CD Pipeline

```
push to main
    ↓
[Lint + Type Check]   ruff + mypy
    ↓
[Unit Tests]          pytest (10 tests, mocked LLM — no API cost)
    ↓
[DORA Lead Time]      Computed from git log, annotated in workflow
```

[![CI Status](https://github.com/KKThella/devex-agent-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/KKThella/devex-agent-platform/actions/workflows/ci.yml)

---

## Roadmap

| Status | Feature |
|---|---|
| ✅ | Multi-agent orchestration (Retrieval + Ranking) |
| ✅ | RAG pipeline + ChromaDB vector store |
| ✅ | Agent memory (episodic + semantic) |
| ✅ | Natural language interface + NL parser |
| ✅ | Python SDK + CLI |
| ✅ | Streamlit interactive demo UI |
| ✅ | Observability + DORA metrics |
| ✅ | GitHub Actions CI/CD |
| 🔜 | Team knowledge base ingestion (Confluence, Notion, ADRs) |
| 🔜 | Slack bot integration |
| 🔜 | VS Code extension |
| 🔜 | Pinecone hosted vector DB for production scale |

---

## Why I Built This

I'm a Staff/Principal Product Manager with 13+ years building AI-powered platforms at Nike. This project is a hands-on prototype to close the gap between PM strategy and engineering execution — specifically around agentic systems, developer tooling, and platform thinking.

The patterns here — multi-agent orchestration, RAG-grounded recommendations, persistent memory, developer-first SDK design — directly mirror the architecture decisions I drive in production systems at scale.

**Related work:** [iHerb Product Recs Demo](https://github.com/KKThella/Recs_Demo) · [LinkedIn](https://linkedin.com/in/kiran-thella)

---

## Local Development

```bash
# Install dependencies
pip install -e ".[dev]"
pip install streamlit chromadb sentence-transformers

# Run tests
pytest tests/ -v --cov=agent_platform

# Run linting
ruff check .
mypy agent_platform sdk cli --ignore-missing-imports

# Launch web UI
streamlit run app.py

# Use CLI
devex recommend "best database for time-series data" --stack python
```

---

*Built by [Kiran Thella](https://linkedin.com/in/kiran-thella) · Multi-agent RAG architecture · Claude-powered · [Live Demo](https://devex-agent-platform-txn.streamlit.app)*
