from click import shell_completion
import os
import logging
from typing import Dict, Any, List, Optional

# LangChain core
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Embeddings

from langchain_huggingface import HuggingFaceEmbeddings

# Project
from backend.src.graph.state import VideoAuditState
from backend.src.services.video_indexer import VideoIndexerService

# parsers format
from backend.src.graph.schemas import AuditResult

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Extracts video metadata and video from url.

    Args:
        state: Current state containing video_url or local_file_path

    Returns:
        Dict with video_metadata, transcript, ocr, and optional error
    """
    video_url = state.get("video_url")
    video_id_input = state.get("video_id", "vid_demo")

    logger.info(f"--[Node:Indexer] Processing: {video_url}")

    local_filename = "temp_audit_video.mp4"

    try:
        vi_service = VideoIndexerService()

        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)
        else:
            raise Exception("Please provide a valid YouTube URL for this test")

        azure_video_id = vi_service.upload_video(local_path, video_name=video_id_input)
        logger.info(f"[Indexer]: Uploaded Video ID: {azure_video_id}")

        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"[Indexer] Deleted local video {local_path}")

        raw_insights = vi_service.wait_for_processing(azure_video_id)

        if not raw_insights:
            raise Exception("Video Indexer returned no insights")

        cleaned_data = vi_service.extract_data(raw_insights)

        logger.info(
            f"[Indexer]: Extracted {len(cleaned_data['ocr_text'])} OCR lines "
            f"and {len(cleaned_data['transcript'])} lines of speech"
        )
        return cleaned_data

    except Exception as e:
        logger.error(f"Video Indexer Failed: {e}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": [],
        }


def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Performs RAG-augmented compliance audit on video transcript and OCR.

    """
    logger.info("--[Node:Auditor] Querying knowledge base & LLM")

    transcript = state.get("transcript", "")

    if not transcript:
        logger.warning("No transcript. Skipping audit.")
        return {
            "final_status": "FAIL",
            "final_report": "No audio/transcript found in the video.",
        }

    # --- Setup LLM, embeddings, vector store ---
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )


    embeddings = HuggingFaceEmbeddings(
    model_name='sentence-transformers/all-MiniLM-L6-v2'
    )

    vector_store = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        embedding_function=embeddings.embed_query,
    )


    # --- RAG retrieval ---
    ocr_texts = state.get("ocr_text") or []
    combined_ocr = "\n".join(ocr_texts)

    retrieved_docs = vector_store.similarity_search(
        query=f"{transcript}\n\n{combined_ocr}", k=3
    )
    logger.info(f"[Auditor]: Retrieved {len(retrieved_docs)} docs from vector store")

    retrieved_rules = "\n\n".join([doc.page_content for doc in retrieved_docs])

    # --- Output parser ---
    parser = PydanticOutputParser(pydantic_object=AuditResult)


    SYSTEM_TEMPLATE = """\
    You are a strict Brand Safety and Compliance Auditor.
    Your job is to audit video content against the provided brand safety guidelines.

    <retrieved_guidelines>
    {retrieved_rules}
    </retrieved_guidelines>

    Analyze the transcript and on-screen text (OCR) below for violations of the above guidelines.
    Return your findings as a structured JSON object that strictly matches the schema below.

    {format_instructions}
    """

    HUMAN_TEMPLATE = """\
    VIDEO METADATA:
    {video_metadata}

    VIDEO TRANSCRIPT:
    {transcript}

    ON-SCREEN TEXT (OCR):
    {combined_ocr}

    Audit the video and return your JSON response now.
    """

    AUDIT_PROMPT = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        ("human", HUMAN_TEMPLATE),
    ])

    chain = AUDIT_PROMPT | llm | parser

    try:
        result: AuditResult = chain.invoke({
            "retrieved_rules": retrieved_rules,
            "format_instructions": parser.get_format_instructions(),
            "video_metadata": str(state.get("video_metadata", {})),
            "transcript": transcript,
            "combined_ocr": combined_ocr,
        })

        logger.info(f"[Auditor]: Audit complete — status={result.final_status}, issues={len(result.compliance_results)}")

        return {
            "compliance_results": [issue.model_dump() for issue in result.compliance_results],
            "final_status": result.final_status,
            "final_report": result.final_report,
        }

    except Exception as e:
        logger.error(f"[Auditor]: Audit chain failed: {e}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "final_report": f"Audit failed due to an internal error: {str(e)}",
        }

