import os
import time
import logging
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_huggingface import HuggingFaceEmbeddings

from backend.src.graph.state import VideoAuditState
from backend.src.services.video_indexer import VideoIndexerService
from backend.src.graph.schemas import AuditResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )


def _build_vector_store(embeddings: HuggingFaceEmbeddings) -> AzureSearch:
    return AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        embedding_function=embeddings.embed_query,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Node 1 — Video Indexer
# ─────────────────────────────────────────────────────────────────────────────

def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Downloads the YouTube video, uploads it to Azure Video Indexer,
    waits for processing, and returns the extracted transcript, OCR,
    keywords and video metadata.
    """
    video_url = state.get("video_url", "")
    video_id = state.get("video_id", "vid_unknown")

    logger.info("[Indexer] Starting — video_id=%s url=%s", video_id, video_url)
    t0 = time.perf_counter()

    local_filename = f"tmp_{video_id}.mp4"

    try:
        service = VideoIndexerService()

        if "youtube.com" not in video_url and "youtu.be" not in video_url:
            raise ValueError(f"Unsupported URL format: {video_url}")

        local_path = service.download_youtube_video(video_url, output_path=local_filename)
        azure_id = service.upload_video(local_path, video_name=video_id)
        logger.info("[Indexer] Uploaded to Azure VI — azure_id=%s", azure_id)

        if os.path.exists(local_path):
            os.remove(local_path)

        raw_insights = service.wait_for_processing(azure_id)
        if not raw_insights:
            raise RuntimeError("Azure Video Indexer returned empty insights")

        extracted = service.extract_data(raw_insights)

        elapsed = round(time.perf_counter() - t0, 2)
        logger.info(
            "[Indexer] Done in %.1fs — %d OCR lines, transcript length=%d chars",
            elapsed,
            len(extracted.get("ocr_text", [])),
            len(extracted.get("transcript", "")),
        )

        return {**extracted, "processing_duration_seconds": elapsed}

    except Exception as exc:
        logger.error("[Indexer] Failed: %s", exc, exc_info=True)
        return {
            "errors": [f"Indexer error: {exc}"],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": [],
            "keywords": [],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Node 2 — Compliance Auditor
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a senior Brand Safety and Regulatory Compliance Auditor specialising in \
digital advertising. You have deep knowledge of FTC guidelines, platform advertising \
policies, and industry-standard disclosure requirements.

Your task is to audit the provided video content against the compliance guidelines \
retrieved below. Be precise, evidence-based, and cite the specific content that \
triggered each finding.

<retrieved_guidelines>
{retrieved_rules}
</retrieved_guidelines>

Rules for your analysis:
- Only flag violations that are clearly supported by the transcript or OCR evidence.
- Assign HIGH severity to issues that carry legal or regulatory risk.
- Assign MEDIUM to issues that pose brand or reputational risk.
- Assign LOW to best-practice deviations with minor impact.
- Populate confidence_score (0.0–1.0) to reflect how certain you are.
- If you can trace the violation to a specific guideline in the retrieved docs, \
  populate rule_reference with the section name or quote.
- Compute risk_score (0–100) as: (HIGH × 30 + MEDIUM × 10 + LOW × 3), capped at 100.

{format_instructions}
"""

_HUMAN_PROMPT = """\
VIDEO METADATA:
{video_metadata}

DETECTED KEYWORDS (from Azure VI):
{keywords}

FULL TRANSCRIPT:
{transcript}

ON-SCREEN TEXT (OCR):
{combined_ocr}

Perform a thorough compliance audit and return your structured JSON response.
"""

_AUDIT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human",  _HUMAN_PROMPT),
])


def compliance_audit_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    RAG-augmented compliance audit node.

    Retrieves the most relevant compliance rules from Azure AI Search,
    then asks Gemini to produce a structured audit report.
    """
    logger.info("[Auditor] Starting compliance audit")

    transcript = state.get("transcript") or ""
    ocr_texts  = state.get("ocr_text") or []
    keywords   = state.get("keywords") or []

    if not transcript.strip():
        logger.warning("[Auditor] No transcript available — cannot audit")
        return {
            "final_status": "FAIL",
            "final_report": "## Audit Incomplete\n\nNo speech transcript was extracted from the video. "
                            "Ensure the video contains audible content and try again.",
            "errors": ["No transcript extracted from video"],
        }

    combined_ocr = "\n".join(ocr_texts)
    rag_query    = f"{transcript}\n\n{combined_ocr}\n\nKeywords: {', '.join(keywords)}"

    # ── Build components ─────────────────────────────────────────────────
    llm = _build_llm()
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = _build_vector_store(embeddings)
    parser = PydanticOutputParser(pydantic_object=AuditResult)

    # ── Retrieve relevant rules ──────────────────────────────────────────
    retrieved_docs = vector_store.similarity_search(query=rag_query, k=4)
    logger.info("[Auditor] Retrieved %d rule docs from vector store", len(retrieved_docs))
    retrieved_rules = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)

    # ── Run audit chain ──────────────────────────────────────────────────
    chain = _AUDIT_PROMPT | llm | parser

    try:
        result: AuditResult = chain.invoke({
            "retrieved_rules":     retrieved_rules,
            "format_instructions": parser.get_format_instructions(),
            "video_metadata":      str(state.get("video_metadata", {})),
            "keywords":            ", ".join(keywords) if keywords else "none detected",
            "transcript":          transcript,
            "combined_ocr":        combined_ocr or "No on-screen text detected",
        })

        violations = [issue.model_dump() for issue in result.compliance_results]
        logger.info(
            "[Auditor] Audit complete — status=%s, violations=%d, risk_score=%s",
            result.final_status,
            len(violations),
            result.risk_score,
        )

        return {
            "compliance_results": violations,
            "final_status":       result.final_status,
            "final_report":       result.final_report,
        }

    except Exception as exc:
        logger.error("[Auditor] Chain failed: %s", exc, exc_info=True)
        return {
            "errors":       [f"Auditor error: {exc}"],
            "final_status": "FAIL",
            "final_report": f"## Audit Failed\n\nAn internal error occurred during analysis:\n\n```\n{exc}\n```",
        }
