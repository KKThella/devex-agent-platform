# DevEx Agent Platform — Hands-On Walkthrough

Run every command below in your Terminal from the repo root.
Each step teaches one concept from the build plan.

---

## 0. One-Time Setup

```bash
cd ~/Career/devex-agent-platform

# Create isolated Python environment (best practice — keeps deps separate from system Python)
python3 -m venv .venv
source .venv/bin/activate        # You'll run this every time you open a new terminal

# Install all dependencies
pip install -e ".[dev]"          # -e means "editable install" — code changes take effect immediately
pip install chromadb sentence-transformers typer rich

# Set your API key (copy from .env.example first)
cp .env.example .env
# Open .env and paste your Anthropic API key:  ANTHROPIC_API_KEY=sk-ant-...
```

**What you just did:** Created a virtual environment (isolated sandbox for this project's Python packages). The `-e` flag means Python reads your source files directly — no reinstall needed when you change code.

---

## 1. Repo Scaffold + PM README

```bash
# See the project structure
find . -type f | grep -v ".git\|.venv\|__pycache__\|.ruff" | sort

# Read the PM-focused README
cat README.md
```

**Concept:** A well-structured repo tells a story. Notice the folder layout:
- `agent_platform/` — the core engine (agents, memory, RAG, LLM, observability)
- `sdk/` — what a developer integrates into their app
- `cli/` — what a developer uses from the terminal
- `tests/` — automated verification

The README is written from a PM lens: problem, architecture diagram, DORA metrics, not just "how to install."

---

## 2. Core Recommendation Engine

```bash
# Open the knowledge base — this is what the engine knows about
cat agent_platform/rag/knowledge_base.py
```

**Concept:** The knowledge base is 25 curated dev tool entries. Each has: name, category, description, strengths, weaknesses, best_for. This structured data is what makes recommendations grounded — not hallucinated.

Categories: `testing`, `observability`, `framework`, `database`, `infra`, `security`, `agent`, `llm`.

```bash
# Explore it interactively in Python
python3 -c "
from agent_platform.rag.knowledge_base import KNOWLEDGE_BASE
print(f'Total tools: {len(KNOWLEDGE_BASE)}')

# See all categories
cats = set(t[\"category\"] for t in KNOWLEDGE_BASE)
print(f'Categories: {sorted(cats)}')

# See one entry in full
import json
testing_tools = [t for t in KNOWLEDGE_BASE if t[\"category\"] == \"testing\"]
print(json.dumps(testing_tools[0], indent=2))
"
```

---

## 3. RAG Pipeline + ChromaDB Vector Store

RAG = Retrieval-Augmented Generation. Instead of asking Claude to guess from memory, we first retrieve relevant tools from our database, then pass them to Claude as context.

```bash
# Look at the retriever
cat agent_platform/rag/retriever.py
```

**Key concept:** ChromaDB converts text (tool descriptions) into numerical vectors (embeddings). When you search, it finds tools whose vectors are mathematically close to your query vector — this is semantic search, not keyword matching.

```bash
# Run the retriever live
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from agent_platform.rag.retriever import RAGRetriever
r = RAGRetriever()

# Semantic search — no exact keyword needed
results = r.search('I need to monitor my API response times', top_k=3)
print('Query: monitor API response times')
print()
for tool in results:
    print(f\"  → {tool['name']} ({tool['category']}) — score: {tool.get('score', 'n/a')}\")
    print(f\"    {tool['description'][:80]}...\")
    print()
"
```

Notice: you searched for "monitor API response times" — it should return observability tools like Prometheus, Grafana, Datadog without those words appearing in your query.

```bash
# Filter by category
python3 -c "
from agent_platform.rag.retriever import RAGRetriever
r = RAGRetriever()
results = r.search('testing my Python services', top_k=4, category='testing')
for t in results:
    print(f\"  {t['name']}: {t['description'][:60]}...\")
"
```

---

## 4. Multi-Agent Orchestration (Retrieval + Ranking Agents)

Two specialized agents working in a pipeline, coordinated by an Orchestrator.

```bash
# Read each agent
cat agent_platform/agents/retrieval_agent.py
cat agent_platform/agents/ranking_agent.py
cat agent_platform/agents/orchestrator.py
```

**How the pipeline works:**
1. **Orchestrator** receives your query + context
2. It calls **RetrievalAgent** → asks Claude: "Given this query, generate 6 tool candidates with relevance scores"
3. It calls **RankingAgent** → asks Claude: "Given these 6 candidates and the user's stack, pick the winner with reasoning"
4. Orchestrator logs metrics + memory, returns final response

```bash
# Run the full pipeline end-to-end (uses your API key)
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from agent_platform.agents.orchestrator import Orchestrator

orc = Orchestrator()
result = orc.recommend(
    query='best way to add observability to a FastAPI service',
    context={'stack': ['Python', 'FastAPI', 'PostgreSQL'], 'team_size': 5},
    session_id='walkthrough-01'
)

print(f'RECOMMENDATION: {result.recommendation.name}')
print(f'Confidence: {result.recommendation.confidence}/100')
print(f'Reasoning: {result.recommendation.reasoning}')
print()
print('Alternatives:')
for alt in result.alternatives:
    print(f'  #{alt.rank} {alt.name} — {alt.when_to_choose}')
print()
print(f'Total latency: {result.latency_ms:.0f}ms')
"
```

**Watch the output carefully:** You'll see a real recommendation with structured reasoning — this is Claude acting as a domain expert, but constrained by your knowledge base.

---

## 5. Agent Memory (Episodic + Semantic)

Two types of memory that mirror how humans remember things.

```bash
cat agent_platform/memory/episodic.py
cat agent_platform/memory/semantic.py
```

**Episodic memory** = short-term, session-scoped. Like remembering what you talked about in a meeting — gone when the process restarts.

**Semantic memory** = long-term, persistent. Stored in ChromaDB on disk. Survives restarts. Like remembering "this team always uses Python."

```bash
# Test episodic memory
python3 -c "
from agent_platform.memory.episodic import EpisodicMemory

mem = EpisodicMemory()
session = 'demo-session'

# Simulate a conversation
mem.add(session, 'user', 'I need a testing framework')
mem.add(session, 'assistant', 'Recommended pytest with 95% confidence')
mem.add(session, 'user', 'What about load testing?')

history = mem.get_history(session)
print(f'Session has {len(history)} turns:')
for turn in history:
    print(f'  [{turn[\"role\"]}] {turn[\"content\"]}')

context = mem.format_for_context(session)
print()
print('Context string passed to Claude:')
print(context)
"
```

```bash
# Test semantic memory (persistent across runs)
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from agent_platform.memory.semantic import SemanticMemory

sem = SemanticMemory()

# Store a fact
sem.store(
    'Team uses pytest + FastAPI + PostgreSQL. Prefers open source tools.',
    metadata={'session': 'demo', 'team': 'platform-eng'}
)

# Recall it later with a related query (semantic similarity, not exact match)
results = sem.recall('what tools does this team use?')
print('Recalled from semantic memory:')
for r in results:
    print(f'  → {r}')
"

# Re-run the recall to prove it persisted
python3 -c "
from agent_platform.memory.semantic import SemanticMemory
sem = SemanticMemory()
results = sem.recall('open source preferences')
print('Still in memory after restart:')
for r in results:
    print(f'  → {r}')
"
```

---

## 6. Natural Language Interface

Translates messy human input into structured API parameters before hitting the agents.

```bash
cat agent_platform/llm/nl_parser.py
```

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from agent_platform.llm.nl_parser import NLParser

parser = NLParser()

# Messy human input
raw = 'hey we are a small startup using node and react, need something to track errors in prod cheaply'
parsed = parser.parse(raw)

print('Raw input:', raw)
print()
print('Parsed:')
print(f'  Query: {parsed.query}')
print(f'  Stack: {parsed.stack}')
print(f'  Constraints: {parsed.constraints}')
print(f'  Team size: {parsed.team_size}')
"
```

**Concept:** LLMs are good at understanding intent from unstructured text. Rather than forcing users to fill out forms, the NL parser extracts structured data (stack, constraints, team_size) that the downstream agents can use precisely.

---

## 7. Developer SDK + CLI

Two ways to consume the platform: programmatically (SDK) and interactively (CLI).

```bash
cat sdk/client.py
cat cli/main.py
```

**SDK** — for developers embedding this in their own tools:

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

from sdk.client import DevExAgent

# This is what an external developer would write
agent = DevExAgent()
result = agent.recommend(
    query='I need a message queue for async job processing',
    stack=['Python', 'Django'],
    constraints=['self-hosted', 'open source']
)

print(f'Recommended: {result.recommendation}')
print(f'Confidence: {result.confidence}%')
print(f'Why: {result.reasoning}')
"
```

**CLI** — for developers using it directly in terminal:

```bash
# Make sure you're in the repo root with .venv active
devex recommend "best database for time-series metrics" --stack prometheus --stack python

# See conversation history
devex history

# Query semantic memory
devex recall "what databases have we discussed"
```

If `devex` command isn't found, run: `pip install -e .` then try again.

---

## 8. Observability + DORA Metrics

```bash
cat agent_platform/observability/metrics.py
```

**DORA = four metrics that measure engineering team health:**
- Deployment Frequency — how often you ship
- Lead Time — PR open → merged to main
- MTTR — how fast you recover from incidents
- Change Failure Rate — % of deploys that cause incidents

```bash
python3 -c "
from agent_platform.observability.metrics import MetricsCollector

m = MetricsCollector()

# Simulate some requests
m.record('testing framework query', latency_ms=420, retrieval_latency_ms=120,
         ranking_latency_ms=280, confidence=95, session_id='s1')
m.record('observability tools query', latency_ms=380, retrieval_latency_ms=100,
         ranking_latency_ms=260, confidence=88, session_id='s1')
m.record('database selection', latency_ms=510, retrieval_latency_ms=150,
         ranking_latency_ms=340, confidence=72, session_id='s2')
m.record_error('broken query', 'Claude API timeout', session_id='s3')

# Simulate deployments for DORA
m.record_deployment('v0.1.0', 'production', success=True, duration_s=45)
m.record_deployment('v0.1.1', 'production', success=True, duration_s=38)
m.record_deployment('v0.1.2', 'production', success=False, duration_s=12)  # rollback

import json
print('=== Metrics Summary ===')
print(json.dumps(m.summary(), indent=2))

print()
print('=== Prometheus Export ===')
print(m.prometheus_export())
"
```

**What to notice:**
- `latency_p50/p95/p99` — percentiles show tail latency, not just averages
- `error_rate_pct` — tracks reliability
- `dora.change_failure_rate_pct` — one bad deploy out of three = 33%
- `prometheus_export()` — this exact format is scraped by Prometheus/Grafana

---

## 9. GitHub Actions CI/CD

```bash
cat .github/workflows/ci.yml
```

**Three jobs in sequence:**

```
push to main
    ↓
[Lint] ruff + mypy  →  catches style/type bugs before they merge
    ↓
[Test] pytest       →  runs all 10 tests with mocked LLM (no API cost)
    ↓
[DORA] lead time    →  measures how long from PR open to merge
```

The tests run WITHOUT hitting the real Claude API — see how `@patch("agent_platform.agents.retrieval_agent.call_claude")` replaces the real call with a mock response. This makes CI fast and free.

```bash
# Run the full test suite locally the same way CI does
pytest tests/ -v --cov=agent_platform

# Run just one test file
pytest tests/test_memory.py -v

# Run with print output visible
pytest tests/test_agents.py -v -s
```

---

## Full End-to-End Run

The ultimate demo — shows all 8 concepts working together:

```bash
python3 -c "
import os, json
from dotenv import load_dotenv
load_dotenv()

from agent_platform.llm.nl_parser import NLParser
from agent_platform.agents.orchestrator import Orchestrator
from agent_platform.observability.metrics import MetricsCollector

parser = NLParser()
orc = Orchestrator()
metrics = MetricsCollector()

raw_input = 'small team, python backend, need to trace slow API calls and set up alerts'
print(f'User says: \"{raw_input}\"')
print()

# Step 1: NL Parser structures the input
parsed = parser.parse(raw_input)
print(f'[NL Parser] Structured → query: {parsed.query}, stack: {parsed.stack}')

# Step 2: Orchestrator runs retrieval → ranking → memory
result = orc.recommend(
    query=parsed.query,
    context={'stack': parsed.stack, 'constraints': parsed.constraints},
    session_id='full-demo'
)

print()
print(f'[Agents] Recommendation: {result.recommendation.name} ({result.recommendation.confidence}% confidence)')
print(f'[Agents] Reasoning: {result.recommendation.reasoning[:120]}...')
print()
print(f'[Agents] Alternatives: {[a.name for a in result.alternatives]}')
print(f'[Agents] Latency: {result.latency_ms:.0f}ms total')
print()

# Step 3: Log to metrics
metrics.record(parsed.query, result.latency_ms, 100, 200, result.recommendation.confidence, 'full-demo')
summary = metrics.summary()
print(f'[Metrics] Requests: {summary[\"request_count\"]} | Avg confidence: {summary[\"confidence_avg\"]}')
"
```

---

## Concept → File Map (Quick Reference)

| Concept | File(s) |
|---|---|
| Repo scaffold | `README.md`, `pyproject.toml` |
| Core rec engine | `agent_platform/rag/knowledge_base.py` |
| RAG + ChromaDB | `agent_platform/rag/retriever.py` |
| Retrieval agent | `agent_platform/agents/retrieval_agent.py` |
| Ranking agent | `agent_platform/agents/ranking_agent.py` |
| Orchestration | `agent_platform/agents/orchestrator.py` |
| Episodic memory | `agent_platform/memory/episodic.py` |
| Semantic memory | `agent_platform/memory/semantic.py` |
| NL interface | `agent_platform/llm/nl_parser.py` |
| LLM client | `agent_platform/llm/client.py` |
| SDK | `sdk/client.py` |
| CLI | `cli/main.py` |
| Metrics + DORA | `agent_platform/observability/metrics.py` |
| CI/CD pipeline | `.github/workflows/ci.yml` |
| Tests | `tests/test_agents.py`, `test_memory.py`, `test_rag.py` |
