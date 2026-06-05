from langgraph.graph import StateGraph, START, END

from backend.src.graph.nodes import index_video_node, compliance_audit_node
from backend.src.graph.state import VideoAuditState


def create_graph() -> StateGraph:
    """
    Builds and compiles the two-node compliance audit workflow:

        START → indexer → compliance_auditor → END

    - indexer:             downloads video, extracts transcript + OCR via Azure VI
    - compliance_auditor:  RAG-augmented LLM audit against indexed rule documents
    """
    builder = StateGraph(VideoAuditState)

    builder.add_node("indexer",             index_video_node)
    builder.add_node("compliance_auditor",  compliance_audit_node)

    builder.add_edge(START,                "indexer")
    builder.add_edge("indexer",            "compliance_auditor")
    builder.add_edge("compliance_auditor", END)

    return builder.compile()


app = create_graph()
