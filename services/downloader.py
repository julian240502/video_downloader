"""Video download service using yt-dlp and optional Facebook API fallback."""

import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp
import requests


# Supported platform URL patterns
YOUTUBE_PATTERNS = [
    r"youtube\.com",
    r"youtu\.be",
    r"youtube\.com/shorts/",
]
FACEBOOK_PATTERNS = [
    r"facebook\.com",
    r"fb\.watch",
    r"fb\.com",
    r"fbcdn\.net",
]


def detect_platform(url: str) -> str:
    """Detect the platform from the URL (youtube, facebook, or generic)."""
    url_lower = url.lower()
    for pattern in YOUTUBE_PATTERNS:
        if re.search(pattern, url_lower):
            return "youtube"
    for pattern in FACEBOOK_PATTERNS:
        if re.search(pattern, url_lower):
            return "facebook"
    return "generic"


def get_yt_dlp_format(quality: str) -> str:
    """Get yt-dlp format selector string for the given quality."""
    quality = quality.lower()
    formats = {
        "best": "best[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "worst": "worst[ext=mp4]+bestaudio[ext=m4a]/worst[ext=mp4]/worst",
        "360p": "best[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[height<=360]",
        "480p": "best[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
        "720p": "best[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
        "1080p": "best[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
    }
    return formats.get(quality, formats["best"])


def download_with_ytdlp(
    url: str,
    quality: str = "best",
    output_dir: Optional[str] = None,
    progress_hook=None,
) -> tuple[str, Optional[str]]:
    """
    Download video using yt-dlp.

    Returns:
        Tuple of (output_path, error_message). error_message is None on success.
    """
    output_dir = output_dir or tempfile.gettempdir()
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    format_selector = get_yt_dlp_format(quality)

    ydl_opts = {
        "format": format_selector,
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "extract_flat": False,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
    }

    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None, "Could not extract video information"

            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                return filename, None
            # yt-dlp might use different extension
            base = Path(filename).stem
            for ext in [".mp4", ".mkv", ".webm"]:
                alt_path = os.path.join(output_dir, base + ext)
                if os.path.exists(alt_path):
                    return alt_path, None

            return filename, None
    except yt_dlp.utils.DownloadError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)


def try_facebook_api(url: str, quality: str, facebook_api_url: str) -> Optional[str]:
    """
    Try to get download URL from Facebook Video Download API.
    Returns direct download URL or None if failed.
    """
    try:
        response = requests.post(
            f"{facebook_api_url.rstrip('/')}/download",
            json={"url": url, "quality": quality},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("download_url"):
                return data["download_url"]
    except Exception:
        pass
    return None


def get_video_info(url: str) -> tuple[Optional[dict], Optional[str]]:
    """
    Get video metadata without downloading.

    Returns:
        Tuple of (info_dict, error_message). info_dict contains title, thumbnail, duration, etc.
    """
    ydl_opts = {
        "quiet": True,
        "extract_flat": False,
        "skip_download": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None, "Could not extract video information"

            return {
                "title": info.get("title", "Unknown"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
            }, None
    except yt_dlp.utils.DownloadError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)
