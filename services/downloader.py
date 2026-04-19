"""Video download service using yt-dlp and optional Facebook API fallback."""

import os
import re
import tempfile
import time
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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

# YouTube query params that are useful for navigation/tracking but not
# required for single-video extraction in this app.
YOUTUBE_REMOVABLE_PARAMS = {
    "index",
    "start_radio",
    "pp",
    "feature",
}


def normalize_video_url(url: str) -> str:
    """
    Normalize supported video URLs before processing.

    Remove YouTube query parameters that can interfere with single-video
    extraction while keeping core identifiers intact.
    """
    if not url:
        return url

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "youtube.com" not in host and "youtu.be" not in host:
        return url

    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    filtered_items = [
        (k, v)
        for k, v in query_items
        if k.lower() not in YOUTUBE_REMOVABLE_PARAMS
    ]

    if len(filtered_items) == len(query_items):
        return url

    normalized_query = urlencode(filtered_items, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            normalized_query,
            parsed.fragment,
        )
    )


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


def subtitle_to_text(subtitle_content: str) -> str:
    """
    Convert VTT/SRT subtitle content into plain readable text.
    """
    lines = subtitle_content.splitlines()
    cleaned_lines = []
    previous_line_key = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip VTT header and metadata
        if line.upper() == "WEBVTT" or line.startswith("NOTE") or line.startswith("Kind:") or line.startswith("Language:"):
            continue

        # Skip cue numbers and timestamp lines
        if line.isdigit():
            continue
        if "-->" in line:
            continue

        # Remove inline VTT/SRT tags and speaker markers
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\{\\an\d+\}", "", line)
        line = re.sub(r"^\[[^\]]+\]\s*", "", line)
        line = line.strip()

        if not line:
            continue

        # Avoid consecutive duplicate lines common in auto-captions
        dedupe_key = line.lower()
        if dedupe_key == previous_line_key:
            continue
        previous_line_key = dedupe_key
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


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
    # Truncate title to 80 bytes + id for uniqueness; restrictfilenames handles invalid chars
    output_template = os.path.join(output_dir, "%(title).80B - %(id)s.%(ext)s")

    format_selector = get_yt_dlp_format(quality)

    ydl_opts = {
        "format": format_selector,
        "outtmpl": output_template,
        "restrictfilenames": True,
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


def download_audio_mp3(
    url: str,
    output_dir: Optional[str] = None,
    progress_hook=None,
) -> tuple[str, Optional[str]]:
    """
    Download audio from video and convert to MP3 using yt-dlp.

    Returns:
        Tuple of (output_path, error_message). error_message is None on success.
    """
    output_dir = output_dir or tempfile.gettempdir()
    # Truncate title to 80 bytes + id for uniqueness; restrictfilenames handles invalid chars
    output_template = os.path.join(output_dir, "%(title).80B - %(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "restrictfilenames": True,
        "quiet": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "extract_flat": False,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
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
            # The audio will have .mp3 extension after post-processing
            base = Path(filename).stem
            mp3_path = os.path.join(output_dir, base + ".mp3")
            
            if os.path.exists(mp3_path):
                return mp3_path, None
            
            # Fallback: check if file exists with original extension
            if os.path.exists(filename):
                return filename, None

            return mp3_path, None
    except yt_dlp.utils.DownloadError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)


def download_transcript_txt(
    url: str,
    output_dir: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """
    Download subtitles/auto-captions and convert them to a TXT transcript.
    """
    output_dir = output_dir or tempfile.gettempdir()
    output_template = os.path.join(output_dir, "%(title).80B - %(id)s.%(ext)s")

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "vtt/srt/best",
        "subtitleslangs": ["fr", "fr-*", "en", "en-*", ".*"],
        "outtmpl": output_template,
        "restrictfilenames": True,
        "quiet": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "extract_flat": False,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
    }

    try:
        start_mtime = time.time()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None, "Could not extract video information"

            media_filename = ydl.prepare_filename(info)
            base_name = Path(media_filename).stem

            subtitle_candidates = []
            for ext in ("vtt", "srt"):
                subtitle_candidates.extend(Path(output_dir).glob(f"{base_name}*.{ext}"))

            subtitle_candidates = [p for p in subtitle_candidates if p.exists() and p.stat().st_mtime >= start_mtime]

            if not subtitle_candidates:
                return None, "No subtitles or automatic captions available for this URL"

            subtitle_candidates = sorted(subtitle_candidates, key=lambda p: len(p.name))
            subtitle_path = subtitle_candidates[0]

            with open(subtitle_path, "r", encoding="utf-8", errors="ignore") as f:
                subtitle_content = f.read()

            transcript_text = subtitle_to_text(subtitle_content)
            if not transcript_text:
                return None, "Subtitles were found but transcript text is empty"

            txt_path = os.path.join(output_dir, f"{base_name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)

            return txt_path, None
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
