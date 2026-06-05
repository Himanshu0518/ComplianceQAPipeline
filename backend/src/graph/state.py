import operator
import time
from typing import Annotated, List, Dict, Optional, TypedDict, Any


class ComplianceIssue(TypedDict):
    category: str
    description: str
    severity: str
    timestamp: Optional[str]
    confidence_score: Optional[float]
    rule_reference: Optional[str]


class VideoAuditState(TypedDict):
    """
    Shared state passed across all nodes in the LangGraph workflow.
    Each node reads from and writes to this object.
    """

    # ── Inputs ───────────────────────────────────────────────────────────
    video_url: str
    video_id: str
    audit_session_id: str

    # ── Indexer outputs ──────────────────────────────────────────────────
    local_file_path: Optional[str]
    video_metadata: Dict[str, Any]
    transcript: Optional[str]
    ocr_text: List[str]
    keywords: List[str]

    # ── Auditor outputs ──────────────────────────────────────────────────
    compliance_results: Annotated[List[ComplianceIssue], operator.add]
    final_status: str        # "PASS" | "FAIL"
    final_report: str        # Markdown summary

    # ── Diagnostics ──────────────────────────────────────────────────────
    processing_duration_seconds: Optional[float]
    errors: Annotated[List[str], operator.add]
