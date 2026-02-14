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
        margin-top: 0.5rem;
    }
    .platform-youtube { background: #ff000020; color: #cc0000; }
    .platform-facebook { background: #1877f220; color: #1877f2; }
    .platform-generic { background: #6b728020; color: #4b5563; }
    
    /* Preview card styling */
    .preview-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .preview-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        color: #1f2937;
    }
    .preview-meta {
        color: #6b7280;
        font-size: 0.9rem;
    }
    
    /* Download button styling */
    .stDownloadButton>button {
        font-size: 1.1rem;
        padding: 0.85rem 2rem;
        min-height: 52px;
        font-weight: 600;
        border-radius: 12px;
        background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
        border: none;
        color: white;
        box-shadow: 0 4px 14px rgba(255, 107, 53, 0.4);
        transition: all 0.2s;
    }
    .stDownloadButton>button:hover {
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.6);
        transform: translateY(-2px);
    }
    
    @media (max-width: 600px) {
        .main-header {
            font-size: 1.5rem;
        }
        .sub-header {
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }
        .stDownloadButton>button {
            position: fixed !important;
            bottom: 16px !important;
            left: 16px !important;
            right: 16px !important;
            z-index: 9999 !important;
            font-size: 1.1rem !important;
            padding: 1.2rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">⬇️ Video Downloader</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Paste a link and get your video instantly</p>',
    unsafe_allow_html=True,
)

# Sidebar settings
with st.sidebar:
    st.subheader("⚙️ Settings")
    facebook_api_url = st.text_input(
        "Facebook API URL (optional)",
        placeholder="http://localhost:8000",
        help="For Facebook videos when yt-dlp fails",
    )
    quality = st.selectbox(
        "📐 Quality",
        options=["best", "1080p", "720p", "480p", "360p", "worst"],
        index=0,
        help="Higher quality = larger file size",
    )
    st.markdown("---")
    st.caption("💡 **How it works:**")
    st.caption("1. Paste your video URL")
    st.caption("2. Preview loads automatically")
    st.caption("3. Download when ready")

# Initialize session state with simpler structure
if "state" not in st.session_state:
    st.session_state.state = {
        "current_url": None,
        "video_info": None,
        "download_status": "idle",  # idle, fetching_info, downloading, ready, error
        "file_path": None,
        "error": None,
    }

if "reset_flag" not in st.session_state:
    st.session_state.reset_flag = False

if "url_input" not in st.session_state:
    st.session_state.url_input = ""

# Handle reset
if st.session_state.reset_flag:
    st.session_state.state = {
        "current_url": None,
        "video_info": None,
        "download_status": "idle",
        "file_path": None,
        "error": None,
    }
    st.session_state.url_input = ""
    st.session_state.reset_flag = False
    # Scroll to top
    st.markdown("""
        <script>
            window.scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)

# Main URL input
url = st.text_input(
    "🔗 Video URL",
    placeholder="Paste YouTube, Shorts, Facebook, or Reels link here...",
    help="Supports: youtube.com, youtu.be, youtube.com/shorts/, facebook.com, fb.watch",
    key="url_input",
)

# Detect if URL changed
url_changed = url != st.session_state.state["current_url"]
if url_changed:
    st.session_state.state["current_url"] = url
    st.session_state.state["video_info"] = None
    st.session_state.state["download_status"] = "idle"
    st.session_state.state["file_path"] = None
    st.session_state.state["error"] = None

# Auto-detect platform and show badge
if url:
    platform = detect_platform(url)
    platform_labels = {
        "youtube": ("YouTube / Shorts", "platform-youtube"),
        "facebook": ("Facebook / Reels", "platform-facebook"),
        "generic": ("Other", "platform-generic"),
    }
    label, css_class = platform_labels.get(platform, ("Unknown", "platform-generic"))
    st.markdown(
        f'<span class="platform-badge {css_class}">📍 {label}</span>',
        unsafe_allow_html=True,
    )
    st.markdown("")  # spacing

# Container for all dynamic content
main_container = st.container()

with main_container:
    # PHASE 1: Auto-fetch video info when URL is provided
    if url and st.session_state.state["video_info"] is None and st.session_state.state["download_status"] == "idle":
        with st.spinner("🔍 Fetching video info..."):
            try:
                info, info_error = get_video_info(url)
                st.session_state.state["video_info"] = info
                if info_error:
                    st.session_state.state["error"] = info_error
                st.rerun()
            except Exception as e:
                st.session_state.state["error"] = str(e)
                st.error(f"❌ Could not fetch video info: {e}")

    # PHASE 2: Show preview and download button
    if st.session_state.state["video_info"]:
        info = st.session_state.state["video_info"]
        
        # Preview card
        col1, col2 = st.columns([1, 2])
        with col1:
            if info.get("thumbnail"):
                st.image(info["thumbnail"], use_container_width=True)
        
        with col2:
            st.markdown(f'<div class="preview-title">{info.get("title", "Unknown title")}</div>', unsafe_allow_html=True)
            
            meta_parts = []
            if info.get("uploader"):
                meta_parts.append(f"👤 {info['uploader']}")
            if info.get("duration"):
                mins = int(info["duration"] // 60)
                secs = int(info["duration"] % 60)
                meta_parts.append(f"⏱️ {mins}:{secs:02d}")
            if info.get("view_count"):
                meta_parts.append(f"👁️ {info['view_count']:,} views")
            
            if meta_parts:
                st.markdown(f'<div class="preview-meta">{" • ".join(meta_parts)}</div>', unsafe_allow_html=True)
        
        st.markdown("")  # spacing

        # PHASE 3: Download logic
        if st.session_state.state["download_status"] == "idle":
            # Show single download button
            col_center = st.columns([1, 2, 1])[1]
            with col_center:
                if st.button("⬇️ Download Video", type="primary", use_container_width=True, key="start_download"):
                    st.session_state.state["download_status"] = "downloading"
                    st.rerun()
        
        elif st.session_state.state["download_status"] == "downloading":
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            output_dir = Path(tempfile.gettempdir()) / "video_downloader"
            output_dir.mkdir(exist_ok=True)
            
            try:
                # Try Facebook API first if applicable
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
                                            status_text.text(f"⬇️ Downloading... {pct}%")
                            tmpf.close()
                            st.session_state.state["file_path"] = tmpf.name
                            st.session_state.state["download_status"] = "ready"
                            st.rerun()
                        except Exception as e:
                            try:
                                tmpf.close()
                                os.remove(tmpf.name)
                            except:
                                pass
                            raise e

                # Fallback to yt-dlp
                if st.session_state.state["download_status"] == "downloading":
                    def progress_hook(d):
                        if d.get("status") == "downloading":
                            try:
                                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                                downloaded = d.get("downloaded_bytes", 0)
                                if total and total > 0:
                                    pct = min(100, int(100 * downloaded / total))
                                    progress_bar.progress(pct / 100)
                                    status_text.text(f"⬇️ Downloading... {pct}%")
                            except:
                                status_text.text("⬇️ Downloading...")
                        elif d.get("status") == "finished":
                            progress_bar.progress(100)
                            status_text.text("✨ Processing...")

                    file_path, error = download_with_ytdlp(
                        url,
                        quality=quality,
                        output_dir=str(output_dir),
                        progress_hook=progress_hook,
                    )

                    if error:
                        st.session_state.state["error"] = error
                        st.session_state.state["download_status"] = "error"
                    elif file_path and os.path.exists(file_path):
                        st.session_state.state["file_path"] = str(file_path)
                        st.session_state.state["download_status"] = "ready"
                    
                    st.rerun()
                    
            except Exception as e:
                st.session_state.state["error"] = str(e)
                st.session_state.state["download_status"] = "error"
                st.rerun()
        
        elif st.session_state.state["download_status"] == "ready":
            # Show save button
            file_path = st.session_state.state["file_path"]
            if file_path and os.path.exists(file_path):
                st.success("✅ Video ready to save!")
                col_center = st.columns([1, 2, 1])[1]
                with col_center:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="💾 Save to Device",
                            data=f,
                            file_name=f"video_{Path(file_path).stem}.mp4",
                            mime="video/mp4",
                            use_container_width=True,
                            type="primary",
                        )
                
                # Option to download another
                if st.button("🔄 Download Another Video", use_container_width=False):
                    st.session_state.reset_flag = True
                    st.rerun()
            else:
                st.error("❌ File not found. Please try again.")
                if st.button("🔄 Retry", type="primary"):
                    st.session_state.state["download_status"] = "idle"
                    st.rerun()
        
        elif st.session_state.state["download_status"] == "error":
            st.error(f"❌ Download failed: {st.session_state.state['error']}")
            if platform == "facebook" and not facebook_api_url:
                st.info("💡 **Tip:** For Facebook videos, try enabling the Facebook API in settings")
            
            if st.button("🔄 Retry Download", type="primary"):
                st.session_state.state["download_status"] = "idle"
                st.session_state.state["error"] = None
                st.rerun()

# Footer
st.markdown("---")
st.caption("🛡️ Supports: YouTube, YouTube Shorts, Facebook, Instagram Reels")