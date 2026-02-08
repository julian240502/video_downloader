"""Streamlit Video Downloader - YouTube, Shorts, Facebook, Reels."""

import os
import tempfile
from pathlib import Path

import requests
import streamlit as st

from services.downloader import (
    detect_platform,
    download_with_ytdlp,
    get_video_info,
    try_facebook_api,
)

# Page config
st.set_page_config(
    page_title="Video Downloader",
    page_icon="⬇️",
    layout="wide",
)

# Custom styles
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #1f2937;
    }
    .sub-header {
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .platform-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .platform-youtube { background: #ff000020; color: #cc0000; }
    .platform-facebook { background: #1877f220; color: #1877f2; }
    .platform-generic { background: #6b728020; color: #4b5563; }
    /* Streamlit button tweaks and mobile adjustments */
    .stButton>button {
        font-size: 1rem;
        padding: 0.75rem 1rem;
    }

    @media (max-width: 600px) {
        .main-header {
            font-size: 1.5rem;
        }
        .sub-header {
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }
        .platform-badge {
            font-size: 0.75rem;
            padding: 0.2rem 0.5rem;
        }
        .stButton>button {
            font-size: 1.05rem;
            padding: 0.9rem 1rem;
        }
        /* Make the single download button fixed and full-width near the bottom on small screens */
        .stButton>button {
            position: fixed !important;
            bottom: 12px !important;
            left: 12px !important;
            right: 12px !important;
            z-index: 9999 !important;
            border-radius: 8px !important;
        }
        /* Reduce horizontal padding on the main container for small screens */
        .reportview-container .main {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">⬇️ Video Downloader</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Download videos from YouTube, Shorts, Facebook & Reels</p>',
    unsafe_allow_html=True,
)

# Sidebar - optional Facebook API
with st.sidebar:
    st.subheader("⚙️ Settings")
    facebook_api_url = st.text_input(
        "Facebook API URL (optional)",
        placeholder="http://localhost:8000",
        help="Use the Facebook Video Download API for Facebook videos when yt-dlp fails. Leave empty to use yt-dlp only.",
    )

# Main form
url = st.text_input(
    "🔗 Video URL",
    placeholder="Paste YouTube, YouTube Shorts, Facebook, or Reels link here...",
    help="Supports: youtube.com, youtu.be, youtube.com/shorts/, facebook.com, fb.watch, fb.com",
)

quality = st.selectbox(
    "📐 Quality",
    options=["best", "1080p", "720p", "480p", "360p", "worst"],
    index=0,
    help="Best = highest available, Worst = lowest (faster download)",
)

# Detect platform when URL is entered
platform = None
if url:
    platform = detect_platform(url)
    platform_labels = {
        "youtube": ("YouTube / Shorts", "platform-youtube"),
        "facebook": ("Facebook / Reels", "platform-facebook"),
        "generic": ("Other", "platform-generic"),
    }
    label, css_class = platform_labels.get(platform, ("Unknown", "platform-generic"))
    st.markdown(
        f'<span class="platform-badge {css_class}">Detected: {label}</span>',
        unsafe_allow_html=True,
    )

if "download_clicked" not in st.session_state:
    st.session_state["download_clicked"] = False

# Single adaptive download button. On desktop it appears inline in the column; on mobile CSS fixes it to the bottom.
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("⬇️ Download Video", type="primary", use_container_width=True, key="download"):
        st.session_state["download_clicked"] = True

if st.session_state.get("download_clicked") and url:
    with st.spinner("Fetching video..."):
        # Try Facebook API first for Facebook URLs (if configured)
        if platform == "facebook" and facebook_api_url:
            download_url = try_facebook_api(url, quality, facebook_api_url)
            if download_url:
                st.success("✅ Video ready via Facebook API!")
                try:
                    r = requests.get(download_url, stream=True, timeout=60)
                    r.raise_for_status()
                    video_data = r.content
                    st.download_button(
                        label="📥 Save Video",
                        data=video_data,
                        file_name="video.mp4",
                        mime="video/mp4",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"Could not fetch video for download: {e}")
                    st.link_button("📥 Open download link", download_url, use_container_width=True)
                st.stop()

        # Use yt-dlp for all platforms
        output_dir = Path(tempfile.gettempdir()) / "video_downloader"
        output_dir.mkdir(exist_ok=True)

        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_hook(d):
            if d["status"] == "downloading":
                try:
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    downloaded = d.get("downloaded_bytes", 0)
                    if total and total > 0:
                        pct = min(100, int(100 * downloaded / total))
                        progress_bar.progress(pct / 100)
                        status_text.text(f"Downloading... {pct}%")
                except Exception:
                    status_text.text("Downloading...")
            elif d["status"] == "finished":
                progress_bar.progress(100)
                status_text.text("Processing...")

        file_path, error = download_with_ytdlp(
            url,
            quality=quality,
            output_dir=str(output_dir),
            progress_hook=progress_hook,
        )

        progress_bar.empty()
        status_text.empty()

        if error:
            st.error(f"❌ Download failed: {error}")

            if platform == "facebook" and not facebook_api_url:
                st.info(
                    "💡 **Tip for Facebook videos:** If yt-dlp fails, you can run the "
                    "[Facebook Video Download API](https://github.com/sh13y/Facebook-Video-Download-API) "
                    "locally and add its URL in the sidebar settings."
                )
        elif file_path and os.path.exists(file_path):
            st.success("✅ Download complete!")
            with open(file_path, "rb") as f:
                st.download_button(
                    label="📥 Save Video",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="video/mp4",
                    use_container_width=True,
                )
            # Clean up temp file after offering download
            try:
                os.remove(file_path)
            except OSError:
                pass

# Optional: Show video info when URL is pasted
if url and not st.session_state.get("download_clicked"):
    with st.expander("Preview video info"):
        info, info_error = get_video_info(url)
        if info:
            col_a, col_b = st.columns([1, 2])
            with col_a:
                if info.get("thumbnail"):
                    st.image(info["thumbnail"], use_container_width=True)
            with col_b:
                st.write(f"**{info.get('title', 'Unknown')}**")
                if info.get("duration"):
                    mins = int(info["duration"] // 60)
                    secs = int(info["duration"] % 60)
                    st.write(f"Duration: {mins}:{secs:02d}")
                if info.get("uploader"):
                    st.write(f"By: {info['uploader']}")
                if info.get("view_count"):
                    st.write(f"Views: {info['view_count']:,}")
        elif info_error:
            st.caption(f"Could not fetch info: {info_error}")

st.markdown("<hr/>", unsafe_allow_html=True)
# Note: single button only — CSS will make it fixed on small screens, so no duplicate needed.
