"""
DevEx Agent Platform — Interactive Demo UI
Run with: streamlit run app.py
"""

import os
import time
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_api_key():
    """Get API key from Streamlit secrets (Cloud) or environment (local)."""
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DevEx Agent Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .main { background-color: #0f1117; }

    /* Pipeline step cards */
    .step-card {
        background: #1e2130;
        border-left: 4px solid #4f8ef7;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .step-card.active  { border-left-color: #f7c948; }
    .step-card.done    { border-left-color: #4caf7d; }

    /* Recommendation card */
    .rec-card {
        background: linear-gradient(135deg, #1a2744 0%, #1e2130 100%);
        border: 1px solid #4f8ef7;
        border-radius: 12px;
        padding: 24px;
        margin-top: 8px;
    }
    .rec-title  { font-size: 2rem; font-weight: 700; color: #ffffff; margin: 0; }
    .rec-cat    { font-size: 0.85rem; color: #8b9cb6; text-transform: uppercase; letter-spacing: 1px; }

    /* Candidate pills */
    .candidate-pill {
        display: inline-block;
        background: #252a3d;
        border: 1px solid #3a4060;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 0.82rem;
        color: #c0cce0;
    }
    .candidate-pill.winner {
        background: #1a3a5c;
        border-color: #4f8ef7;
        color: #7eb8ff;
        font-weight: 600;
    }

    /* Section headers */
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #8b9cb6;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 6px;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []       # list of {query, result, latency}
if "session_id" not in st.session_state:
    st.session_state.session_id = f"demo-{int(time.time())}"
if "metrics" not in st.session_state:
    st.session_state.metrics = []       # raw metric dicts
if "prefill_query" not in st.session_state:
    st.session_state.prefill_query = ""


# ── Cached resource: load heavy objects once ──────────────────────────────────
@st.cache_resource(show_spinner="Loading agent platform...")
def load_platform():
    from agent_platform.agents.orchestrator import Orchestrator
    from agent_platform.llm.nl_parser import NLParser

    # Initialize RAGRetriever with graceful fallback
    rag = None
    try:
        from agent_platform.rag.retriever import RAGRetriever
        rag = RAGRetriever()
    except Exception as e:
        st.warning(f"ChromaDB unavailable: {str(e)[:100]}. Running in LLM-only mode.")

    # Initialize Orchestrator, which will also attempt SemanticMemory init
    try:
        orchestrator = Orchestrator(rag_retriever=rag)
    except Exception as e:
        st.error(f"Failed to initialize Orchestrator: {str(e)}")
        st.stop()

    return orchestrator, NLParser(), rag


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 DevEx Agent Platform")
    st.caption("AI-powered developer tool recommender")
    st.divider()

    # API key check
    api_key = get_api_key()
    if api_key and api_key.startswith("sk-"):
        st.success("✅ API key connected", icon="🔑")
    else:
        st.error("⚠️ No API key found. Add ANTHROPIC_API_KEY to .env or Streamlit secrets")
        st.stop()

    st.divider()

    # Architecture diagram (text-based, always visible)
    st.markdown("### 🏗️ How it works")
    st.markdown("""
    ```
    Your question
         ↓
    [NL Parser]
    Structures intent
         ↓
    [Retrieval Agent]
    Finds 6 candidates
    from knowledge base
         ↓
    [Ranking Agent]
    Picks the winner
    with reasoning
         ↓
    Recommendation ✓
    ```
    """)

    st.divider()

    # Session history
    st.markdown("### 📜 This session")
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            with st.expander(f"Q{len(st.session_state.history) - i}: {h['query'][:35]}...", expanded=False):
                st.write(f"**→** {h['rec_name']} ({h['confidence']}%)")
                st.caption(f"Latency: {h['latency_ms']:.0f}ms")
    else:
        st.caption("No queries yet — ask something below!")

    st.divider()
    if st.button("🔄 Reset session", use_container_width=True):
        st.session_state.history = []
        st.session_state.metrics = []
        st.session_state.session_id = f"demo-{int(time.time())}"
        st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("# DevEx Agent Platform")
st.markdown("*Ask anything about developer tooling — watch the multi-agent pipeline reason through it.*")
st.divider()

# ── Input form ────────────────────────────────────────────────────────────────
col_input, col_options = st.columns([3, 2])

# Set the widget key value BEFORE rendering so Streamlit persists it across reruns
if st.session_state.prefill_query:
    st.session_state["text_area_query"] = st.session_state.prefill_query
    st.session_state.prefill_query = ""

with col_input:
    user_query = st.text_area(
        "What are you trying to solve?",
        placeholder="e.g. We're a 5-person Python team, need to add observability to our FastAPI service without a big ops burden",
        height=100,
        key="text_area_query",
    )

with col_options:
    selected_stack = st.multiselect(
        "Your tech stack (optional)",
        ["Python", "Node.js", "Go", "Java", "FastAPI", "Django", "React",
         "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", "GCP"],
        placeholder="Select languages/frameworks...",
    )
    constraints = st.text_input(
        "Constraints (optional)",
        placeholder="e.g. open source, self-hosted, free tier",
    )

# Example queries
st.markdown('<p class="section-label">Try an example</p>', unsafe_allow_html=True)
example_cols = st.columns(4)
examples = [
    "Best testing framework for async Python APIs",
    "How do I trace slow database queries in production?",
    "We need a message queue — what should we use?",
    "Cheapest way to monitor a side project",
]
for i, ex in enumerate(examples):
    if example_cols[i].button(f"💡 {ex[:28]}...", use_container_width=True, key=f"ex_{i}"):
        st.session_state.prefill_query = ex
        st.rerun()

st.divider()

# ── Run button ────────────────────────────────────────────────────────────────
run_col, _ = st.columns([1, 3])
run_btn = run_col.button("▶ Get Recommendation", type="primary", use_container_width=True, disabled=not user_query.strip())

# ── Pipeline execution + results ──────────────────────────────────────────────
if run_btn and user_query.strip():

    orchestrator, nl_parser, rag_retriever = load_platform()

    st.markdown("### ⚙️ Pipeline execution")
    pipeline_container = st.container()

    with pipeline_container:
        # ── Step 1: NL Parser ──────────────────────────────────────────────
        step1 = st.empty()
        step1.markdown("""
        <div class="step-card active">
        <b>🔍 Step 1 — NL Parser</b><br>
        <small style="color:#8b9cb6">Structuring your natural language input...</small>
        </div>
        """, unsafe_allow_html=True)

        parsed = nl_parser.parse(user_query)
        # Merge UI selections with parsed output
        final_stack = list(set((parsed.stack or []) + selected_stack))
        final_constraints = ([constraints] if constraints else []) + (parsed.constraints or [])

        step1.markdown(f"""
        <div class="step-card done">
        <b>✅ Step 1 — NL Parser</b><br>
        <small style="color:#4caf7d">Structured query extracted</small><br><br>
        <b>Query:</b> {parsed.query}<br>
        <b>Stack:</b> {", ".join(final_stack) if final_stack else "not specified"}<br>
        <b>Constraints:</b> {", ".join(final_constraints) if final_constraints else "none"}
        </div>
        """, unsafe_allow_html=True)

        # ── Step 2: Retrieval Agent ────────────────────────────────────────
        step2 = st.empty()
        step2.markdown("""
        <div class="step-card active">
        <b>📚 Step 2 — Retrieval Agent</b><br>
        <small style="color:#8b9cb6">Searching knowledge base + asking Claude for 6 candidates...</small>
        </div>
        """, unsafe_allow_html=True)

        # We'll run the full orchestrator below, but show retrieval-style preview from RAG
        try:
            rag_hits = rag_retriever.search(parsed.query, top_k=6)
            rag_names = [h["name"] for h in rag_hits]
        except Exception:
            rag_names = ["searching..."]

        step2.markdown(f"""
        <div class="step-card done">
        <b>✅ Step 2 — Retrieval Agent</b><br>
        <small style="color:#4caf7d">6 candidates identified from knowledge base</small><br><br>
        <b>Candidates:</b><br>
        {"".join(f'<span class="candidate-pill">{n}</span>' for n in rag_names)}
        </div>
        """, unsafe_allow_html=True)

        # ── Step 3: Ranking Agent ──────────────────────────────────────────
        step3 = st.empty()
        step3.markdown("""
        <div class="step-card active">
        <b>🏆 Step 3 — Ranking Agent</b><br>
        <small style="color:#8b9cb6">Claude is reasoning through tradeoffs to pick the winner...</small>
        </div>
        """, unsafe_allow_html=True)

        # Run the full orchestrator (retrieval + ranking via Claude)
        t0 = time.time()
        try:
            result = orchestrator.recommend(
                query=parsed.query,
                context={
                    "stack": final_stack,
                    "constraints": final_constraints,
                    "team_size": parsed.team_size or "unknown",
                },
                session_id=st.session_state.session_id,
            )
            success = True
        except Exception as e:
            success = False
            error_msg = str(e)

        total_ms = (time.time() - t0) * 1000

        if success:
            rec = result.ranking.recommendation
            alts = result.ranking.alternatives or []

            step3.markdown(f"""
            <div class="step-card done">
            <b>✅ Step 3 — Ranking Agent</b><br>
            <small style="color:#4caf7d">Winner selected with {rec.confidence}% confidence</small><br><br>
            <b>Winner:</b> <span class="candidate-pill winner">{rec.name}</span>
            {"".join(f'<span class="candidate-pill">{a.name}</span>' for a in alts[:3])}
            </div>
            """, unsafe_allow_html=True)

            # ── Recommendation card ────────────────────────────────────────
            st.divider()
            st.markdown("### 🎯 Recommendation")

            st.markdown(f"""
            <div class="rec-card">
                <p class="rec-cat">Top Recommendation</p>
                <p class="rec-title">{rec.name}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")

            conf_col, lat_col, _ = st.columns([2, 2, 3])
            conf_col.metric("Confidence", f"{rec.confidence}%")
            lat_col.metric("Pipeline latency", f"{total_ms:.0f}ms")

            st.progress(rec.confidence / 100)

            st.markdown("**Why this tool?**")
            st.info(rec.reasoning)

            if rec.tradeoffs:
                st.markdown("**Tradeoffs to consider**")
                st.warning(rec.tradeoffs)

            if rec.getting_started:
                st.markdown("**Getting started**")
                st.code(rec.getting_started, language="bash")

            if alts:
                st.markdown("**Alternatives worth considering**")
                alt_cols = st.columns(min(len(alts), 3))
                for i, alt in enumerate(alts[:3]):
                    with alt_cols[i]:
                        st.markdown(f"**#{alt.rank} {alt.name}**")
                        st.caption(alt.when_to_choose)

            if hasattr(result.ranking, "avoid") and result.ranking.avoid:
                st.markdown("**Avoid**")
                st.error(result.ranking.avoid)

            # ── Log to session history ─────────────────────────────────────
            st.session_state.history.append({
                "query": user_query,
                "rec_name": rec.name,
                "confidence": rec.confidence,
                "latency_ms": total_ms,
            })
            st.session_state.metrics.append({
                "latency_ms": total_ms,
                "confidence": rec.confidence,
            })

        else:
            step3.markdown(f"""
            <div class="step-card" style="border-left-color:#e05c5c">
            <b>❌ Step 3 — Ranking Agent error</b><br>
            <small style="color:#e05c5c">{error_msg}</small>
            </div>
            """, unsafe_allow_html=True)
            st.error(f"Pipeline error: {error_msg}")


# ── Metrics panel (shows after at least one query) ────────────────────────────
if st.session_state.metrics:
    st.divider()
    st.markdown("### 📊 Session metrics")

    m_col1, m_col2, m_col3 = st.columns(3)
    latencies = [m["latency_ms"] for m in st.session_state.metrics]
    confidences = [m["confidence"] for m in st.session_state.metrics]

    m_col1.metric("Queries this session", len(st.session_state.metrics))
    m_col2.metric("Avg latency", f"{sum(latencies)/len(latencies):.0f}ms")
    m_col3.metric("Avg confidence", f"{sum(confidences)/len(confidences):.0f}%")

    if len(latencies) > 1:
        import pandas as pd
        df = pd.DataFrame({
            "Query #": list(range(1, len(latencies) + 1)),
            "Latency (ms)": latencies,
            "Confidence (%)": confidences,
        })
        chart_col1, chart_col2 = st.columns(2)
        chart_col1.line_chart(df.set_index("Query #")["Latency (ms)"], height=150)
        chart_col2.line_chart(df.set_index("Query #")["Confidence (%)"], height=150)


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("DevEx Agent Platform · Built by Kiran Thella · Multi-agent RAG architecture · Claude-powered")
