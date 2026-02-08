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
if "download_ready" not in st.session_state:
    st.session_state["download_ready"] = False
if "download_file_path" not in st.session_state:
    st.session_state["download_file_path"] = None
if "download_error" not in st.session_state:
    st.session_state["download_error"] = None

# Single adaptive load -> save flow: first click = load, then same area becomes save when ready.
col1, col2, col3 = st.columns([1, 2, 1])
download_container = col2.empty()

with download_container:
    if not st.session_state.get("download_ready"):
        if st.button("⬇️ Load Video", type="primary", use_container_width=True, key="load"):
            st.session_state["download_clicked"] = True
            st.session_state["download_error"] = None
    else:
        # File ready: show save button
        file_path = st.session_state.get("download_file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.download_button(
                    label="📥 Save Video",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="video/mp4",
                    use_container_width=True,
                )
        else:
            st.info("Le fichier préparé est introuvable. Relancer le chargement.")
            if st.button("⬇️ Retry Load", use_container_width=True, key="retry"):
                st.session_state["download_clicked"] = True
                st.session_state["download_ready"] = False
                st.session_state["download_error"] = None

# If user requested load and URL provided, perform fetching (shows progress)
if st.session_state.get("download_clicked") and url and not st.session_state.get("download_ready"):
    output_dir = Path(tempfile.gettempdir()) / "video_downloader"
    output_dir.mkdir(exist_ok=True)

    # Replace the button in-place with progress widgets so the user sees immediate feedback
    progress_bar = download_container.progress(0)
    status_text = download_container.empty()

    # Try Facebook API first (stream to temp file)
    try:
        if platform == "facebook" and facebook_api_url:
            download_url = try_facebook_api(url, quality, facebook_api_url)
            if download_url:
                tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=str(output_dir))
                try:
                    with requests.get(download_url, stream=True, timeout=60) as r:
                        r.raise_for_status()
                        total = int(r.headers.get("Content-Length", 0) or 0)
                        written = 0
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                tmpf.write(chunk)
                                written += len(chunk)
                                if total:
                                    pct = min(100, int(100 * written / total))
                                    progress_bar.progress(pct / 100)
                                    status_text.text(f"Downloading... {pct}%")
                    tmpf.close()
                    st.session_state["download_file_path"] = tmpf.name
                    st.session_state["download_ready"] = True
                    st.session_state["download_clicked"] = False
                except Exception as e:
                    try:
                        tmpf.close()
                    except Exception:
                        pass
                    try:
                        os.remove(tmpf.name)
                    except Exception:
                        pass
                    st.session_state["download_error"] = str(e)

        # If not ready via API, fallback to yt-dlp with progress hooks
        if not st.session_state.get("download_ready"):
            def progress_hook(d):
                if d.get("status") == "downloading":
                    try:
                        total = d.get("total_bytes") or d.get("total_bytes_estimate")
                        downloaded = d.get("downloaded_bytes", 0)
                        if total and total > 0:
                            pct = min(100, int(100 * downloaded / total))
                            progress_bar.progress(pct / 100)
                            status_text.text(f"Downloading... {pct}%")
                    except Exception:
                        status_text.text("Downloading...")
                elif d.get("status") == "finished":
                    progress_bar.progress(100)
                    status_text.text("Processing...")

            file_path, error = download_with_ytdlp(
                url,
                quality=quality,
                output_dir=str(output_dir),
                progress_hook=progress_hook,
            )

            # Clear status widgets before replacing with save button
            progress_bar.empty()
            status_text.empty()

            if error:
                st.session_state["download_error"] = error
            elif file_path and os.path.exists(file_path):
                st.session_state["download_file_path"] = str(file_path)
                st.session_state["download_ready"] = True
                st.session_state["download_clicked"] = False
    except Exception as e:
        st.session_state["download_error"] = str(e)

    # Show result or error in the same container immediately
    if st.session_state.get("download_ready"):
        # replace container contents with the save button so user can immediately click it
        download_container.empty()
        file_path = st.session_state.get("download_file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                download_container.download_button(
                    label="📥 Save Video",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="video/mp4",
                    use_container_width=True,
                )
    elif st.session_state.get("download_error"):
        download_container.empty()
        download_container.error(f"❌ Download failed: {st.session_state.get('download_error')}")
        if platform == "facebook" and not facebook_api_url:
            download_container.info(
                "💡 **Tip for Facebook videos:** If yt-dlp échoue, exécutez l'API Facebook localement "
                "et ajoutez son URL dans les paramètres sidebar."
            )
        if download_container.button("⬇️ Retry Load", use_container_width=True, key="retry2"):
            st.session_state["download_clicked"] = True
            st.session_state["download_ready"] = False
            st.session_state["download_error"] = None

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
