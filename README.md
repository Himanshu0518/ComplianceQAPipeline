# 🛡️ Compliance QA Pipeline

An automated **brand-safety and regulatory compliance auditor** for video ad content. Paste a YouTube URL, and the pipeline downloads the video, extracts speech and on-screen text via **Azure Video Indexer**, retrieves relevant compliance rules from **Azure AI Search**, and uses **Gemini 2.5 Flash** to produce a structured audit report — all orchestrated with **LangGraph**.

---

## ✨ Features

- 🎬 **YouTube ingestion** — downloads any public video via `yt-dlp`
- 🗣️ **Speech-to-text + OCR** — powered by Azure Video Indexer
- 📚 **RAG-based rule retrieval** — compliance rules indexed in Azure AI Search
- 🤖 **LLM audit** — Gemini 2.5 Flash returns structured violations (category, severity, timestamp)
- 🖥️ **Streamlit UI** — clean dark-mode dashboard with stage progress, violation cards, and full report
- 🔗 **LangGraph workflow** — stateful two-node graph (Indexer → Auditor)

---

## 🏗️ Architecture

```
YouTube URL
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  LangGraph Workflow                                     │
│                                                         │
│  ┌──────────────┐        ┌──────────────────────────┐  │
│  │   Indexer    │──────▶ │        Auditor           │  │
│  │              │        │                          │  │
│  │ yt-dlp       │        │ HuggingFace Embeddings   │  │
│  │ Azure VI     │        │ Azure AI Search (RAG)    │  │
│  │ Transcript   │        │ Gemini 2.5 Flash (LLM)   │  │
│  │ OCR          │        │ Pydantic output parser   │  │
│  └──────────────┘        └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
    │
    ▼
AuditResult { compliance_results, final_status, final_report }
```

---

## 📁 Project Structure

```
ComplianceQAPipeline/
├── app.py                        # Streamlit UI (run this)
├── main.py                       # CLI runner (for quick tests)
├── pyproject.toml                # Dependencies (uv/pip)
├── .env                          # API keys (not committed)
│
└── backend/
    ├── data/
    │   ├── 1001a-influencer-guide-508_1.pdf   # Compliance rule doc
    │   └── youtube-ad-specs.pdf               # Ad specs rule doc
    │
    └── src/
        ├── api/
        │   └── server.py                      # (FastAPI stub — future)
        │
        ├── graph/
        │   ├── workflow.py     # LangGraph StateGraph definition
        │   ├── nodes.py        # index_video_node + audio_content_node
        │   ├── state.py        # VideoAuditState TypedDict
        │   └── schemas.py      # Pydantic output schemas
        │
        └── services/
            └── video_indexer.py  # Azure Video Indexer wrapper
```

---

## ⚙️ Setup

### 1. Prerequisites

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`
- Azure subscription with:
  - **Azure Video Indexer** account
  - **Azure AI Search** index (with compliance docs already ingested)
- Google AI Studio API key (Gemini)
- `ffmpeg` installed and on your PATH (required by `yt-dlp`)

### 2. Install dependencies

```bash
# With uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```env
# Google Gemini
GOOGLE_API_KEY=your_google_api_key

# Azure Video Indexer
AZURE_VI_ACCOUNT_ID=your_vi_account_id
AZURE_VI_LOCATION=trial          # e.g. trial, eastus
AZURE_VI_NAME=your_vi_resource_name
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_RESOURCE_GROUP=your_resource_group

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX_NAME=your_index_name
AZURE_SEARCH_API_KEY=your_search_api_key
```

> **Auth note:** Azure Video Indexer uses `DefaultAzureCredential`. Make sure you are logged in via `az login` or have a managed identity / service principal configured.

### 4. Index your compliance documents

Before running audits, ingest your rule PDFs into Azure AI Search. The `backend/data/` folder contains the reference documents:

- `1001a-influencer-guide-508_1.pdf` — FTC influencer disclosure guidelines
- `youtube-ad-specs.pdf` — YouTube advertising specifications

Use the Azure portal, the Azure SDK, or your preferred ingestion script to chunk and embed these into the search index.

---

## 🚀 Running the App

### Streamlit UI (recommended)

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### CLI (quick test)

```bash
python main.py
```

This runs a hardcoded YouTube URL through the pipeline and prints results to stdout.

---

## 🖥️ UI Walkthrough

| Section | Description |
|---|---|
| **URL input** | Paste any public YouTube URL |
| **Stage badges** | Live status for Indexer and Auditor stages |
| **Verdict banner** | PASS ✅ or FAIL ❌ with video ID |
| **Metrics row** | Total / High / Medium / Low violation counts |
| **Violation cards** | Per-issue severity, category, description, timestamp |
| **Full Audit Report** | Markdown report generated by the LLM |
| **Raw Data (debug)** | Transcript text, OCR lines, video metadata |

---

## 🧩 Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | Gemini 2.5 Flash via `langchain-google-genai` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) |
| Vector store | Azure AI Search |
| Video processing | Azure Video Indexer |
| Video download | `yt-dlp` |
| UI | Streamlit |
| Validation | Pydantic v2 |
| Environment | Python 3.12 + uv |

---

## 🔮 Roadmap

- [ ] FastAPI backend (`backend/src/api/server.py`) for headless/API use
- [ ] Batch auditing — process a playlist or CSV of URLs
- [ ] PDF report export
- [ ] Custom rule upload directly from the UI
- [ ] Webhook / Slack notification on FAIL verdict

---

## 📄 License

MIT
