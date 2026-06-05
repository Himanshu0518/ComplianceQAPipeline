import os
import time
import logging
import requests
import yt_dlp
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

_VI_API_BASE = "https://api.videoindexer.ai"
_ARM_BASE     = "https://management.azure.com"


class VideoIndexerService:
    """
    Thin wrapper around Azure Video Indexer.

    Handles authentication, upload, polling, and insight extraction.
    All Azure credentials are read from environment variables.
    """

    def __init__(self):
        self.account_id      = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location        = os.getenv("AZURE_VI_LOCATION", "trial")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group  = os.getenv("AZURE_RESOURCE_GROUP")
        self.vi_name         = os.getenv("AZURE_VI_NAME")
        self._credential     = DefaultAzureCredential()

    # ── Auth ─────────────────────────────────────────────────────────────

    def _arm_token(self) -> str:
        """Returns a short-lived Azure Resource Manager bearer token."""
        return self._credential.get_token(f"{_ARM_BASE}/.default").token

    def _vi_token(self) -> str:
        """Exchanges an ARM token for a Video Indexer account token."""
        url = (
            f"{_ARM_BASE}/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2024-01-01"
        )
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {self._arm_token()}"},
            json={"permissionType": "Contributor", "scope": "Account"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["accessToken"]

    # ── Ingestion ─────────────────────────────────────────────────────────

    def download_youtube_video(self, url: str, output_path: str = "temp_video.mp4") -> str:
        """Downloads a public YouTube video to disk using yt-dlp."""
        logger.info("[VI] Downloading: %s", url)
        opts = {
            "format":   "best[ext=mp4]/best",
            "outtmpl":  output_path,
            "quiet":    True,
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        logger.info("[VI] Download complete → %s", output_path)
        return output_path

    def upload_video(self, video_path: str, video_name: str) -> str:
        """Uploads a local MP4 to Azure Video Indexer and returns the Azure video ID."""
        token   = self._vi_token()
        api_url = f"{_VI_API_BASE}/{self.location}/Accounts/{self.account_id}/Videos"
        params  = {
            "accessToken":    token,
            "name":           video_name,
            "privacy":        "Private",
            "indexingPreset": "Default",
        }
        logger.info("[VI] Uploading %s to Azure...", video_path)
        with open(video_path, "rb") as fh:
            resp = requests.post(api_url, params=params, files={"file": fh}, timeout=120)
        resp.raise_for_status()
        azure_id = resp.json()["id"]
        logger.info("[VI] Uploaded — azure_id=%s", azure_id)
        return azure_id

    def wait_for_processing(self, azure_video_id: str, poll_interval: int = 60) -> dict:
        """
        Polls the Video Indexer index endpoint until the video reaches
        'Processed' state, then returns the full insights JSON.
        """
        url = f"{_VI_API_BASE}/{self.location}/Accounts/{self.account_id}/Videos/{azure_video_id}/Index"
        logger.info("[VI] Waiting for Azure to process video %s...", azure_video_id)

        while True:
            token = self._vi_token()
            resp  = requests.get(url, params={"accessToken": token}, timeout=30)
            resp.raise_for_status()
            data  = resp.json()
            state = data.get("state")

            if state == "Processed":
                logger.info("[VI] Processing complete.")
                return data
            elif state == "Failed":
                raise RuntimeError(f"Azure Video Indexer failed for video {azure_video_id}")
            elif state == "Quarantined":
                raise RuntimeError(
                    f"Video {azure_video_id} was quarantined (possible copyright / policy violation)"
                )

            logger.info("[VI] State=%s — retrying in %ds", state, poll_interval)
            time.sleep(poll_interval)

    # ── Extraction ────────────────────────────────────────────────────────

    def extract_data(self, vi_json: dict) -> dict:
        """
        Parses the raw Video Indexer insights JSON into the fields
        expected by VideoAuditState.
        """
        transcript_parts: list[str] = []
        ocr_lines:        list[str] = []
        keyword_labels:   list[str] = []

        for video in vi_json.get("videos", []):
            insights = video.get("insights", {})

            for seg in insights.get("transcript", []):
                text = (seg.get("text") or "").strip()
                if text:
                    transcript_parts.append(text)

            for seg in insights.get("ocr", []):
                text = (seg.get("text") or "").strip()
                if text:
                    ocr_lines.append(text)

            for kw in insights.get("keywords", []):
                label = (kw.get("text") or kw.get("name") or "").strip()
                if label:
                    keyword_labels.append(label)

        summary = vi_json.get("summarizedInsights", {})
        duration_secs = (
            summary.get("duration", {}).get("seconds")
            or vi_json.get("videos", [{}])[0].get("insights", {}).get("duration", {}).get("seconds")
        )

        named_people = [
            p.get("name") for p in summary.get("faces", []) if p.get("name")
        ]
        sentiment = summary.get("sentiments", [])

        return {
            "transcript":     " ".join(transcript_parts),
            "ocr_text":       ocr_lines,
            "keywords":       list(dict.fromkeys(keyword_labels)),   # deduplicated, order-preserved
            "video_metadata": {
                "duration_seconds": duration_secs,
                "platform":         "youtube",
                "named_people":     named_people,
                "sentiment":        sentiment,
                "transcript_lines": len(transcript_parts),
                "ocr_line_count":   len(ocr_lines),
            },
        }
