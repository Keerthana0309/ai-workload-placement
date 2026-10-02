"""
AI Workload Placement — Decision Engine (Web App)
===================================================
Streamlit web UI wrapping the same decision logic as decide.py.

SETUP (one-time):
    pip install streamlit

HOW TO RUN:
    streamlit run app.py

This opens a local web page (usually http://localhost:8501) where you can
answer the questions via dropdowns instead of typing in a terminal — much
easier to demo to someone.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Same decision logic as decide.py — kept in sync manually for now.
# ---------------------------------------------------------------------------
def decide(task_type, privacy, latency, connectivity, budget):
    if privacy == "high":
        return (
            "LOCAL / DEVICE",
            "Privacy requirement is high — data can't leave the device/org, "
            "so cloud is off the table regardless of other factors."
        )

    if connectivity == "offline":
        return (
            "LOCAL / DEVICE",
            "Connectivity is unreliable or offline — cloud inference isn't "
            "viable without a stable connection."
        )

    if task_type == "complex" and budget != "free":
        return (
            "CLOUD",
            "Task requires complex reasoning — small local models "
            "(like llama3.2:1b) aren't strong enough for this yet, and "
            "budget allows for a cloud-hosted model."
        )

    if latency == "strict" and connectivity == "reliable":
        return (
            "CLOUD",
            "Latency tolerance is strict and connectivity is reliable. "
            "Benchmark data (local llama3.2:1b vs. cloud Haiku 4.5 on "
            "summarization) showed cloud was actually faster on average "
            "(~1.2s vs ~2.6s) for this kind of simple task — a real, "
            "non-obvious finding worth trusting over the 'local is always "
            "faster' assumption."
        )

    if budget == "free" and task_type == "simple":
        return (
            "LOCAL / DEVICE",
            "Task is simple and budget is free/minimal — a small local "
            "model handles this well at zero marginal cost per request."
        )

    return (
        "CLOUD",
        "No hard constraints pushing toward local, and benchmark data "
        "showed cloud offers comparable or better latency at trivial "
        "cost (~$0.0001/request) for simple tasks. Default to cloud "
        "unless you have a specific reason to stay local."
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI Workload Placement", page_icon="🧭")

st.title("🧭 AI Workload Placement — Decision Engine")
st.caption(
    "Given an AI workload, where should it run — device or cloud? "
    "Answer a few quick questions to get a recommendation, backed by "
    "real benchmark data (local llama3.2:1b vs. cloud Claude Haiku 4.5)."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    task_type = st.radio(
        "Task type",
        ["simple", "complex"],
        help="Simple = classification, summarization, short Q&A. "
             "Complex = multi-step reasoning, agentic tasks.",
    )
    privacy = st.radio(
        "Privacy requirement",
        ["low", "high"],
        help="High = data cannot leave the device/organization.",
    )
    latency = st.radio(
        "Latency tolerance",
        ["strict", "normal", "relaxed"],
        index=1,
        help="Strict = needs near-real-time response (<1s). "
             "Relaxed = a few seconds or more is fine.",
    )

with col2:
    connectivity = st.radio(
        "Connectivity",
        ["reliable", "offline"],
        help="Offline = intermittent or no internet connection expected.",
    )
    budget = st.radio(
        "Budget",
        ["free", "flexible"],
        help="Free = no budget for per-request API costs.",
    )

st.divider()

if st.button("Get Recommendation", type="primary"):
    recommendation, reason = decide(task_type, privacy, latency, connectivity, budget)

    if recommendation == "LOCAL / DEVICE":
        st.success(f"### Recommendation: {recommendation}")
    else:
        st.info(f"### Recommendation: {recommendation}")

    st.write(f"**Why:** {reason}")

st.divider()
st.caption(
    "v1 — rule-based logic grounded in a real local-vs-cloud benchmark. "
    "Not a platform, not a commitment — just a fast answer. "
    "[View the benchmark data and source on GitHub](https://github.com/Keerthana0309/ai-workload-placement)"
)
