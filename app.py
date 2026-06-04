import uuid
import logging
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="Compliance QA Pipeline",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    .stApp { background: #0d0f14; color: #e2e8f0; }

    section[data-testid="stSidebar"] { background: #111318 !important; border-right: 1px solid #1e2230; }
    section[data-testid="stSidebar"] * { color: #a0aec0 !important; }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: #e2e8f0 !important; }

    .header-strip {
        background: linear-gradient(135deg, #0f1623 0%, #141b2d 100%);
        border: 1px solid #1e3a5f; border-radius: 12px;
        padding: 28px 36px; margin-bottom: 28px;
        display: flex; align-items: center; gap: 18px;
    }
    .header-strip h1 {
        font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem;
        font-weight: 600; color: #63b3ed; margin: 0; letter-spacing: -0.5px;
    }
    .header-strip p { color: #718096; font-size: 0.88rem; margin: 4px 0 0 0; }

    .card { background: #111318; border: 1px solid #1e2230; border-radius: 10px; padding: 22px 24px; margin-bottom: 16px; }
    .card-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: #4a5568; margin-bottom: 10px; }

    .badge { display: inline-block; padding: 4px 14px; border-radius: 20px; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.06em; }
    .badge-pass   { background: #0d2a1f; color: #48bb78; border: 1px solid #276749; }
    .badge-fail   { background: #2d1515; color: #fc8181; border: 1px solid #9b2c2c; }
    .badge-running{ background: #1a2540; color: #63b3ed; border: 1px solid #2b4c7e; }

    .sev-high   { background:#2d1515; color:#fc8181; border:1px solid #9b2c2c; border-radius:4px; padding:2px 8px; font-size:0.72rem; font-family:'IBM Plex Mono',monospace; font-weight:600; }
    .sev-medium { background:#2d2011; color:#f6ad55; border:1px solid #975a16; border-radius:4px; padding:2px 8px; font-size:0.72rem; font-family:'IBM Plex Mono',monospace; font-weight:600; }
    .sev-low    { background:#1a2540; color:#63b3ed; border:1px solid #2b4c7e; border-radius:4px; padding:2px 8px; font-size:0.72rem; font-family:'IBM Plex Mono',monospace; font-weight:600; }

    .violation-row { border-left: 3px solid; padding: 12px 16px; margin-bottom: 10px; border-radius: 0 8px 8px 0; background: #0d0f14; }
    .vrow-high   { border-color: #fc8181; }
    .vrow-medium { border-color: #f6ad55; }
    .vrow-low    { border-color: #63b3ed; }
    .vrow-title  { font-size: 0.88rem; font-weight: 500; color: #e2e8f0; margin-bottom: 4px; }
    .vrow-desc   { font-size: 0.82rem; color: #718096; line-height: 1.5; }
    .vrow-ts     { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #4a5568; margin-top: 6px; }

    .stTextInput > div > div > input {
        background: #111318 !important; border: 1px solid #1e2230 !important;
        color: #e2e8f0 !important; border-radius: 8px !important;
        font-family: 'IBM Plex Mono', monospace !important; font-size: 0.88rem !important;
        padding: 10px 14px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #2b4c7e !important; box-shadow: 0 0 0 2px rgba(99,179,237,0.12) !important;
    }

    .stButton > button {
        background: #1a3a5c !important; color: #90cdf4 !important;
        border: 1px solid #2b4c7e !important; border-radius: 8px !important;
        font-family: 'IBM Plex Mono', monospace !important; font-size: 0.82rem !important;
        font-weight: 600 !important; letter-spacing: 0.05em !important;
        padding: 10px 26px !important; transition: all 0.18s !important;
    }
    .stButton > button:hover {
        background: #2b4c7e !important; border-color: #63b3ed !important; color: #bee3f8 !important;
    }

    [data-testid="stMetric"] { background: #111318; border: 1px solid #1e2230; border-radius: 8px; padding: 16px 20px; }
    [data-testid="stMetricLabel"] { color: #4a5568 !important; font-size: 0.75rem !important; }
    [data-testid="stMetricValue"] { color: #e2e8f0 !important; font-family: 'IBM Plex Mono', monospace !important; }

    .streamlit-expanderHeader { background: #111318 !important; border: 1px solid #1e2230 !important; border-radius: 8px !important; color: #a0aec0 !important; font-size: 0.84rem !important; }
    .streamlit-expanderContent { background: #0d0f14 !important; border: 1px solid #1e2230 !important; border-top: none !important; }

    .stSpinner > div { border-top-color: #63b3ed !important; }
    hr { border-color: #1e2230 !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d0f14; }
    ::-webkit-scrollbar-thumb { background: #1e2230; border-radius: 3px; }

    /* ── Streamlit top-right toolbar (Running / Connected status) ── */
    [data-testid="stStatusWidget"] {
        background: #111318 !important;
        border: 1px solid #1e2230 !important;
        border-radius: 8px !important;
        padding: 2px 10px !important;
    }
    [data-testid="stStatusWidget"] * {
        color: #4a5568 !important;
        fill: #4a5568 !important;
    }
    /* Top toolbar bar itself */
    [data-testid="stToolbar"] {
        background: #0d0f14 !important;
        border-bottom: 1px solid #1e2230 !important;
    }
    [data-testid="stToolbar"] * {
        color: #4a5568 !important;
    }
    /* The very top decoration bar (colored line Streamlit adds) */
    [data-testid="stDecoration"] {
        background: #1e2230 !important;
        display: none !important;
    }
    /* Main menu (hamburger) */
    #MainMenu {
        visibility: hidden;
    }
    header[data-testid="stHeader"] {
        background: #0d0f14 !important;
        border-bottom: 1px solid #1e2230 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compliance-ui")


@st.cache_resource(show_spinner=False)
def load_workflow():
    from backend.src.graph.workflow import app as workflow_app
    return workflow_app


# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🛡️ Compliance QA")
    st.markdown("---")
    st.markdown("### Pipeline Stages")
    st.markdown(
        """
        <div style="font-size:0.82rem;line-height:2.2;color:#718096;">
        &nbsp;① &nbsp;<b style="color:#e2e8f0;">Indexer</b><br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Download → Azure VI upload<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcript + OCR extraction<br><br>
        &nbsp;② &nbsp;<b style="color:#e2e8f0;">Auditor</b><br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;RAG retrieval from rule docs<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Gemini Flash structured audit<br>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### Quick Examples")
    if st.button("▶  Sample Ad 1", key="ex_1"):
        st.session_state["url_input"] = "https://youtu.be/dT7S75eYhcQ"
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.72rem;color:#4a5568;'>LangGraph · Azure Video Indexer<br>"
        "Gemini 2.5 Flash · Azure AI Search</p>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="header-strip">
        <div style="font-size:2.4rem;">🛡️</div>
        <div>
            <h1>Compliance QA Pipeline</h1>
            <p>Automated brand-safety &amp; regulatory audit for video ad content
               &nbsp;·&nbsp; Powered by LangGraph + Gemini + Azure</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════
# INPUT
# ══════════════════════════════════════════════════════════════════════════
col_input, col_btn = st.columns([5, 1], gap="small")

with col_input:
    video_url = st.text_input(
        "YouTube Video URL",
        value=st.session_state.get("url_input", ""),
        placeholder="https://youtu.be/...",
        label_visibility="collapsed",
        key="url_input",
    )

with col_btn:
    run_audit = st.button("▶ Run Audit", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# AUDIT EXECUTION
# ══════════════════════════════════════════════════════════════════════════
if run_audit:
    if not video_url or not video_url.strip():
        st.warning("⚠️  Please enter a YouTube URL before running the audit.")
        st.stop()

    session_id = str(uuid.uuid4())
    video_id   = f"vid_{session_id[:8]}"

    stage_col1, stage_col2 = st.columns(2)

    with stage_col1:
        st.markdown(
            '<div class="card"><div class="card-title">Stage 1 — Indexer</div>'
            '<span class="badge badge-running">⏳ Running</span></div>',
            unsafe_allow_html=True,
        )
    with stage_col2:
        st.markdown(
            '<div class="card"><div class="card-title">Stage 2 — Auditor</div>'
            '<span class="badge" style="background:#1a1f2e;color:#4a5568;border:1px solid #1e2230;">Waiting</span></div>',
            unsafe_allow_html=True,
        )

    status_box = st.empty()
    status_box.info("🔄  Downloading & indexing video via Azure Video Indexer… (this may take a few minutes)")

    try:
        workflow = load_workflow()
        initial_inputs = {
            "video_url": video_url.strip(),
            "video_id": video_id,
            "compliance_results": [],
            "errors": [],
        }

        with st.spinner("Running compliance pipeline…"):
            final_state = workflow.invoke(initial_inputs)

        status_box.empty()

        with stage_col1:
            st.markdown(
                '<div class="card"><div class="card-title">Stage 1 — Indexer</div>'
                '<span class="badge badge-pass">✓ Done</span></div>',
                unsafe_allow_html=True,
            )
        with stage_col2:
            st.markdown(
                '<div class="card"><div class="card-title">Stage 2 — Auditor</div>'
                '<span class="badge badge-pass">✓ Done</span></div>',
                unsafe_allow_html=True,
            )

        final_status       = final_state.get("final_status", "UNKNOWN")
        compliance_results = final_state.get("compliance_results", [])
        final_report       = final_state.get("final_report", "")
        errors             = final_state.get("errors", [])
        video_metadata     = final_state.get("video_metadata", {})
        transcript         = final_state.get("transcript", "")

        high   = [i for i in compliance_results if (i.get("severity") or "").upper() == "HIGH"]
        medium = [i for i in compliance_results if (i.get("severity") or "").upper() == "MEDIUM"]
        low    = [i for i in compliance_results if (i.get("severity") or "").upper() == "LOW"]

        st.markdown("---")

        verdict_color  = "#48bb78" if final_status == "PASS" else "#fc8181"
        verdict_bg     = "#0d2a1f" if final_status == "PASS" else "#2d1515"
        verdict_border = "#276749" if final_status == "PASS" else "#9b2c2c"
        verdict_icon   = "✅" if final_status == "PASS" else "❌"

        st.markdown(
            f"""
            <div style="background:{verdict_bg};border:1px solid {verdict_border};border-radius:10px;
                        padding:20px 28px;margin-bottom:20px;display:flex;align-items:center;gap:16px;">
                <div style="font-size:2.2rem;">{verdict_icon}</div>
                <div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:1.4rem;
                                font-weight:600;color:{verdict_color};">{final_status}</div>
                    <div style="font-size:0.82rem;color:#718096;margin-top:2px;">
                        Video ID: <code style="color:#a0aec0;">{video_id}</code>
                        &nbsp;·&nbsp; {len(compliance_results)} violation(s) found
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Issues", len(compliance_results))
        m2.metric("🔴 High",   len(high))
        m3.metric("🟠 Medium", len(medium))
        m4.metric("🔵 Low",    len(low))

        st.markdown("<br>", unsafe_allow_html=True)

        if compliance_results:
            st.markdown(
                '<div class="card-title" style="font-family:\'IBM Plex Mono\',monospace;font-size:0.72rem;'
                'letter-spacing:0.12em;text-transform:uppercase;color:#4a5568;margin-bottom:12px;">'
                'Violations Detected</div>',
                unsafe_allow_html=True,
            )
            for issue in compliance_results:
                sev       = (issue.get("severity") or "LOW").upper()
                sev_cls   = f"sev-{sev.lower()}"   if sev in ("HIGH","MEDIUM","LOW") else "sev-low"
                row_cls   = f"vrow-{sev.lower()}"  if sev in ("HIGH","MEDIUM","LOW") else "vrow-low"
                ts_html   = (f'<div class="vrow-ts">⏱ {issue.get("timestamp")}</div>'
                             if issue.get("timestamp") else "")
                st.markdown(
                    f"""
                    <div class="violation-row {row_cls}">
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                            <span class="{sev_cls}">{sev}</span>
                            <span class="vrow-title">{issue.get("category","—")}</span>
                        </div>
                        <div class="vrow-desc">{issue.get("description","")}</div>
                        {ts_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success("🎉  No violations detected — video passes all compliance checks.")

        if final_report:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📋  Full Audit Report", expanded=True):
                st.markdown(final_report)

        if transcript or video_metadata:
            with st.expander("🔍  Raw Extracted Data (debug)"):
                if video_metadata:
                    st.json(video_metadata)
                if transcript:
                    st.markdown("**Transcript**")
                    st.text_area("", value=transcript, height=200, label_visibility="collapsed")
                ocr = final_state.get("ocr_text", [])
                if ocr:
                    st.markdown("**OCR Lines**")
                    for line in ocr:
                        st.markdown(f"- {line}")

        if errors:
            with st.expander("⚠️  Pipeline Errors"):
                for err in errors:
                    st.error(err)

    except Exception as exc:
        status_box.empty()
        logger.error(f"UI Error: {exc}", exc_info=True)
        st.error(f"**Pipeline failed:** {exc}")
        with st.expander("Full traceback"):
            import traceback
            st.code(traceback.format_exc(), language="python")

# ══════════════════════════════════════════════════════════════════════════
# EMPTY STATE
# ══════════════════════════════════════════════════════════════════════════
else:
    st.markdown(
        """
        <div class="card" style="text-align:center;padding:48px 36px;">
            <div style="font-size:3rem;margin-bottom:16px;">🎬</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:1rem;color:#63b3ed;margin-bottom:8px;">
                Ready to audit
            </div>
            <div style="color:#718096;font-size:0.88rem;max-width:480px;margin:0 auto;line-height:1.7;">
                Paste a YouTube URL above and click <b style="color:#a0aec0;">▶ Run Audit</b>.<br>
                The pipeline downloads the video, extracts transcript &amp; on-screen text,
                then checks for brand-safety violations against your compliance rulebook.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    hw1, hw2, hw3 = st.columns(3)
    cards = [
        ("📥", "Ingest",   "YouTube video is downloaded and uploaded to Azure Video Indexer for speech-to-text and OCR processing."),
        ("🔍", "Extract",  "Transcript and on-screen text (OCR) are extracted from Azure Video Indexer insights."),
        ("⚖️", "Audit",    "Gemini 2.5 Flash performs RAG-augmented compliance check against your indexed rule documents."),
    ]
    for col, (icon, title, desc) in zip([hw1, hw2, hw3], cards):
        col.markdown(
            f"""
            <div class="card" style="text-align:center;padding:28px 20px;">
                <div style="font-size:2rem;margin-bottom:10px;">{icon}</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:0.82rem;
                            color:#63b3ed;margin-bottom:8px;">{title}</div>
                <div style="color:#718096;font-size:0.80rem;line-height:1.6;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
