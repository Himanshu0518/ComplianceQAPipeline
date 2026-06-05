"""
CLI entry point for the Compliance QA Pipeline.

Usage:
    python main.py

Runs the full LangGraph workflow against a test YouTube URL and
prints a formatted compliance report to stdout.
"""

import uuid
import json
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

from backend.src.graph.workflow import app  # noqa: E402 (import after env load)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger("compliance-cli")


def run(video_url: str = "https://youtu.be/dT7S75eYhcQ") -> None:
    session_id = str(uuid.uuid4())
    video_id   = f"vid_{session_id[:8]}"

    logger.info("Session %s — auditing: %s", session_id, video_url)

    inputs = {
        "video_url":        video_url,
        "video_id":         video_id,
        "audit_session_id": session_id,
        "compliance_results": [],
        "errors":           [],
    }

    print("\n" + "─" * 60)
    print("  INPUT")
    print("─" * 60)
    print(json.dumps(inputs, indent=2))

    final_state = app.invoke(inputs)

    print("\n" + "─" * 60)
    print("  COMPLIANCE AUDIT REPORT")
    print("─" * 60)
    print(f"  Video ID : {final_state.get('video_id')}")
    print(f"  Status   : {final_state.get('final_status')}")
    print(f"  Duration : {final_state.get('processing_duration_seconds', '—')}s")

    results = final_state.get("compliance_results", [])
    print(f"\n  Violations ({len(results)} found):")
    if results:
        for issue in results:
            sev  = issue.get("severity", "?")
            cat  = issue.get("category", "?")
            desc = issue.get("description", "")
            conf = issue.get("confidence_score")
            conf_str = f"  [conf={conf:.0%}]" if conf is not None else ""
            print(f"  • [{sev}] {cat}{conf_str}")
            print(f"    {desc}")
    else:
        print("  None — video passes all checks.")

    print("\n  Summary:")
    print(final_state.get("final_report", "No report generated."))

    errors = final_state.get("errors", [])
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for err in errors:
            print(f"  ⚠  {err}")

    print("─" * 60 + "\n")


if __name__ == "__main__":
    run()
