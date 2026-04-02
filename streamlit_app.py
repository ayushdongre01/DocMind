import asyncio
from pathlib import Path
import time

import streamlit as st
import inngest
from dotenv import load_dotenv
import os
import requests

load_dotenv()

st.set_page_config(
    page_title="DocMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet">

<style>

/* Restore Streamlit material icons */
span.material-symbols-rounded,
span.material-symbols-outlined,
span.material-icons {
    font-family: "Material Symbols Outlined" !important;
}

/* ── Dark canvas ── */
.stApp {
    background: #0a0a0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,.18) 0%, transparent 70%),
        radial-gradient(ellipse 40% 30% at 85% 80%, rgba(168,85,247,.10) 0%, transparent 60%);
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }

/* ── Reduce excessive main container padding ── */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}

/* ─────────────────────────────────────────────
   SIDEBAR FIXES
   - Natural flow (no position:absolute footer)
   - Larger, readable font sizes (15-16px base)
   - Proper padding-bottom so tips don't overlap
───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0f0f18 !important;
    border-right: 1px solid rgba(99,102,241,.15) !important;
}

/* Sidebar scrollable inner content */
[data-testid="stSidebar"] > div:first-child {
    padding: 1.2rem 1rem 2rem 1rem !important;
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow-y: auto;
    height: 100%;
    box-sizing: border-box;
}

[data-testid="stSidebar"] {
    color: #c4c4d4 !important;
    font-family: 'Sora', sans-serif !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #e8e8f0 !important; }

/* ── Hero ── */
.hero-wrap {
    text-align: center;
    padding: 1.2rem 1rem 1.6rem;   /* reduced from 3.5rem top */
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    background: rgba(99,102,241,.12);
    border: 1px solid rgba(99,102,241,.3);
    border-radius: 999px;
    padding: .3rem .9rem;
    font-size: .75rem;
    font-weight: 600;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: #a5b4fc;
    margin-bottom: 1rem;
}
.hero-title {
    font-size: clamp(1.75rem, 3.5vw, 2.6rem);
    font-weight: 700;
    line-height: 1.2;
    background: linear-gradient(135deg, #e8e8f8 0%, #a5b4fc 55%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 .7rem;
}
.hero-sub {
    font-size: .97rem;
    color: #6b7099;
    margin: 0 auto;
    line-height: 1.65;
    font-weight: 300;
    text-align: center;
}

/* ── Section label ── */
.section-label {
    display: flex;
    align-items: center;
    gap: .5rem;
    font-size: .8rem;
    font-weight: 600;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: #6b7099;
    margin-bottom: .6rem;
}

/* ── Cards — tighter padding ── */
.card {
    background: linear-gradient(145deg, #13131f 0%, #0f0f1a 100%);
    border: 1px solid rgba(99,102,241,.14);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;        /* reduced from 1.6/1.8 */
    margin-bottom: 1rem;
    box-shadow: 0 4px 32px rgba(0,0,0,.35);
    transition: border-color .2s;
}
.card:hover { border-color: rgba(99,102,241,.32); }

/* ── Upload zone hint ── */
.upload-hint {
    text-align: center;
    padding: .35rem 0 0;           /* reduced top/bottom */
    color: #454566;
    font-size: .82rem;
}

/* ── Status pills ── */
.pill-success {
    display: inline-flex; align-items: center; gap: .4rem;
    background: rgba(52,211,153,.1);
    border: 1px solid rgba(52,211,153,.25);
    border-radius: 999px;
    padding: .28rem .85rem;
    color: #34d399;
    font-size: .84rem;
    font-weight: 500;
    margin-top: .5rem;
}
.pill-info {
    display: inline-flex; align-items: center; gap: .4rem;
    background: rgba(99,102,241,.1);
    border: 1px solid rgba(99,102,241,.25);
    border-radius: 999px;
    padding: .28rem .85rem;
    color: #a5b4fc;
    font-size: .84rem;
    font-weight: 500;
    margin-top: .4rem;
}

/* ── Response box ── */
.response-box {
    background: linear-gradient(145deg, #0d0d1a 0%, #0a0a14 100%);
    border: 1px solid rgba(99,102,241,.2);
    border-left: 3px solid #6366f1;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    color: #d4d4e8;
    font-size: .95rem;
    line-height: 1.75;
    margin-top: .6rem;
    font-family: 'Sora', sans-serif;
}

/* ── Sources chip ── */
.source-chip {
    display: inline-flex;
    align-items: center;
    gap: .35rem;
    background: rgba(99,102,241,.08);
    border: 1px solid rgba(99,102,241,.18);
    border-radius: 8px;
    padding: .28rem .7rem;
    font-size: .78rem;
    color: #8b8bbb;
    font-family: 'JetBrains Mono', monospace;
    margin: .2rem .2rem 0 0;
}

/* ── Divider ── */
.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,.25), transparent);
    margin: 1.5rem 0;
}

/* ── Button overrides ── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: .9rem !important;
    padding: .65rem 2rem !important;
    letter-spacing: .03em !important;
    transition: opacity .2s, transform .15s !important;
    box-shadow: 0 4px 20px rgba(99,102,241,.35) !important;
}
.stButton > button:hover {
    opacity: .88 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Form submit button (Ask) ── */
[data-testid="stFormSubmitButton"] > button {
    width: 100% !important;
    padding: .72rem 1.2rem !important;
    font-size: .92rem !important;
    margin-top: .5rem !important;
}

/* ── Input fields ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    background: #0d0d1a !important;
    border: 1px solid rgba(99,102,241,.2) !important;
    border-radius: 10px !important;
    color: #d4d4e8 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: .93rem !important;
    padding: .5rem .75rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: rgba(99,102,241,.55) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.1) !important;
}

/* ── File uploader — compact ── */
[data-testid="stFileUploader"] {
    background: rgba(99,102,241,.04) !important;
    border: 1.5px dashed rgba(99,102,241,.25) !important;
    border-radius: 12px !important;
    transition: border-color .2s !important;
    padding: .5rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(99,102,241,.5) !important;
}
[data-testid="stFileUploader"] * { color: #8b8bbb !important; }

/* ── Labels ── */
label,
.stTextInput label,
.stNumberInput label {
    color: #7b7baa !important;
    font-size: .85rem !important;
    font-weight: 500 !important;
    margin-bottom: .2rem !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(99,102,241,.06) !important;
    border: 1px solid rgba(99,102,241,.15) !important;
    border-radius: 10px !important;
    color: #8b8bbb !important;
    font-size: .85rem !important;
    font-family: 'Sora', sans-serif !important;
}
.streamlit-expanderContent {
    background: rgba(99,102,241,.03) !important;
    border: 1px solid rgba(99,102,241,.1) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* ── Sidebar: section heading style ── */
.sb-section-head {
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #454566 !important;
    margin: 1rem 0 .6rem;
    font-family: 'Sora', sans-serif;
}

/* ── Sidebar: step item ── */
.sb-step {
    display: flex;
    gap: .65rem;
    margin-bottom: .85rem;
    align-items: flex-start;
}
.sb-step-icon { font-size: 1.05rem; margin-top: .05rem; flex-shrink: 0; }
.sb-step-title {
    font-size: .93rem;
    font-weight: 600;
    color: #c8c8e0 !important;
    line-height: 1.3;
    font-family: 'Sora', sans-serif;
}
.sb-step-desc {
    font-size: .82rem;
    color: #5e5e7e !important;
    line-height: 1.55;
    font-family: 'Sora', sans-serif;
    margin-top: .1rem;
}

/* ── Sidebar: tip item ── */
.sb-tip {
    display: flex;
    gap: .5rem;
    margin-bottom: .6rem;
    align-items: flex-start;
}
.sb-tip-bullet {
    color: #6366f1 !important;
    font-size: .9rem;
    margin-top: .08rem;
    flex-shrink: 0;
}
.sb-tip-text {
    font-size: .84rem;
    color: #5e5e7e !important;
    line-height: 1.6;
    font-family: 'Sora', sans-serif;
}

/* ── Sidebar: footer — NOT absolute, stays in flow ── */
.sb-footer {
    margin-top: 1.6rem;
    padding-top: .9rem;
    border-top: 1px solid rgba(99,102,241,.12);
    font-size: .75rem;
    color: #3a3a58 !important;
    text-align: center;
    line-height: 1.7;
    font-family: 'Sora', sans-serif;
}

/* ── Sidebar brand header ── */
.sb-brand {
    display: flex;
    align-items: center;
    gap: .55rem;
    margin-bottom: .45rem;
}
.sb-brand-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e8e8f8 !important;
    font-family: 'Sora', sans-serif;
}
.sb-tagline {
    font-size: .83rem;
    color: #555577 !important;
    line-height: 1.6;
    font-family: 'Sora', sans-serif;
}
.sb-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,.2), transparent);
    margin: .9rem 0;
}
            
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined' !important;
    font-size: 20px;
}
/* Fix sidebar collapse arrow visibility */
[data-testid="collapsedControl"] span {
    color: white !important;
}

/* Ensure SVG icons also appear white */
[data-testid="collapsedControl"] svg {
    fill: white !important;
}
</style>
""", unsafe_allow_html=True)


# ── Backend helpers (unchanged) ─────────────────────────────────────────────

@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    #return inngest.Inngest(app_id="rag_app", is_production=False)
    return inngest.Inngest(app_id="rag_app", is_production=True)


def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_path.write_bytes(file.getbuffer())
    return file_path


async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()
    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": str(pdf_path.resolve()),
                "source_id": pdf_path.name,
            },
        )
    )


async def send_rag_query_event(question: str, top_k: int):
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={"question": question, "top_k": top_k},
        )
    )
    return result[0]


def _inngest_api_base() -> str:
    return os.getenv("INNGEST_API_BASE")


def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("data", [])


def wait_for_run_output(event_id: str, timeout_s: float = 1200.0, poll_interval_s: float = 0.5) -> dict:
    start = time.time()
    last_status = None
    while True:
        runs = fetch_runs(event_id)
        if runs:
            run = runs[0]
            status = run.get("status")
            last_status = status or last_status
            if status in ("Completed", "Succeeded", "Success", "Finished"):
                return run.get("output") or {}
            if status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Function run {status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for run output (last status: {last_status})")
        time.sleep(poll_interval_s)


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    # Brand header
    st.markdown("""
    <div class="sb-brand">
        <span style="font-size:1.4rem">🧠</span>
        <span class="sb-brand-name">DocMind</span>
    </div>
    <div class="sb-tagline">
        Intelligent document analysis powered by retrieval-augmented generation.
    </div>
    <div class="sb-divider"></div>
    """, unsafe_allow_html=True)

    # How it works
    steps = [
        ("📄", "Upload a PDF", "Drop your document into the upload zone."),
        ("⚙️", "Ingestion", "The pipeline chunks and embeds your PDF."),
        ("💬", "Ask anything", "Type a question about the document."),
        ("✨", "Get answers", "AI retrieves context and generates an answer."),
    ]
    st.markdown('<div class="sb-section-head">How it works</div>', unsafe_allow_html=True)
    for icon, title, desc in steps:
        st.markdown(f"""
        <div class="sb-step">
            <span class="sb-step-icon">{icon}</span>
            <div>
                <div class="sb-step-title">{title}</div>
                <div class="sb-step-desc">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # Tips
    tips = [
        "Upload a PDF to enable question answering over the document.",
        "Higher chunk count (top_k) retrieves more context but may slow responses.",
        "Ask specific questions to get more accurate answers.",
    ]
    st.markdown('<div class="sb-section-head">Tips</div>', unsafe_allow_html=True)
    for tip in tips:
        st.markdown(f"""
        <div class="sb-tip">
            <span class="sb-tip-bullet">›</span>
            <span class="sb-tip-text">{tip}</span>
        </div>
        """, unsafe_allow_html=True)

    # Footer — in normal document flow, no position:absolute
    st.markdown("""
    <div class="sb-footer">
        Built with Inngest · LangChain · Streamlit<br>
        © 2026 DocMind
    </div>
    """, unsafe_allow_html=True)


# ── Main content ─────────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">✦ &nbsp;RAG-Powered &nbsp;✦</div>
    <h1 class="hero-title">Chat with your Documents</h1>
    <p class="hero-sub">
        Upload any PDF and ask questions in plain language.
        DocMind retrieves the most relevant passages and generates precise answers — instantly.
    </p>
</div>
<div class="fancy-divider"></div>
""", unsafe_allow_html=True)

# ── Two-column layout ────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

# ── LEFT: Upload ─────────────────────────────────────────────────────────────
with col_left:
    st.markdown("""
    <div class="card">
        <div class="section-label">📄 &nbsp;Document Upload</div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop a PDF here or click to browse",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="visible",
    )

    st.markdown('<div class="upload-hint">Supports PDF · Max 200 MB</div>', unsafe_allow_html=True)

    if uploaded is not None:
        with st.spinner("Ingesting document…"):
            path = save_uploaded_pdf(uploaded)
            asyncio.run(send_rag_ingest_event(path))
            time.sleep(0.3)

        st.markdown(f"""
        <div class="pill-success">✓ &nbsp;Ingested: <strong>{path.name}</strong></div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close card


# ── RIGHT: Q&A ────────────────────────────────────────────────────────────────
with col_right:
    st.markdown("""
    <div class="card">
        <div class="section-label">💬 &nbsp;Ask a Question</div>
    """, unsafe_allow_html=True)

    with st.form("rag_query_form"):
        question = st.text_input(
            "Your question",
            placeholder="e.g. What are the key findings in chapter 3?",
        )

        top_k = st.number_input(
            "Chunks to retrieve (top_k)",
            min_value=1, max_value=20, value=5, step=1,
            help="Higher = more context, slower response",
        )

        submitted = st.form_submit_button("✦ Ask DocMind", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close card

    # ── Answer section ────────────────────────────────────────────────────────
    if submitted and question.strip():
        with st.spinner("Generating answer…"):
            event_id = asyncio.run(send_rag_query_event(question.strip(), int(top_k)))
            output = wait_for_run_output(event_id)
            answer = output.get("answer", "")
            sources = output.get("sources", [])

        # Answer card
        st.markdown("""
        <div style="margin-top:.4rem">
            <div class="section-label">✨ &nbsp;Answer</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="response-box">{answer or "<em style='color:#454566'>No answer was returned.</em>"}</div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Sources
        if sources:
            with st.expander(f"📎  Sources  ({len(sources)} references)", expanded=False):
                chips = "".join(
                    f'<span class="source-chip">📄 {s}</span>'
                    for s in sources
                )
                st.markdown(f'<div style="padding:.4rem 0">{chips}</div>', unsafe_allow_html=True)

    elif submitted and not question.strip():
        st.markdown("""
        <div class="pill-info" style="margin-top:.5rem">⚠ &nbsp;Please enter a question before submitting.</div>
        """, unsafe_allow_html=True)