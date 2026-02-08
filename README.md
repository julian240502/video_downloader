# Video Downloader

A simple Streamlit app to download online videos from **YouTube** (including Shorts), **Facebook** (including Reels), and other platforms supported by yt-dlp.

## Features

- **Multi-platform**: YouTube, YouTube Shorts, Facebook, Facebook Reels, and more
- **Quality selection**: Best, 1080p, 720p, 480p, 360p, or worst
- **Optional Facebook API**: Use the [Facebook Video Download API](https://github.com/sh13y/Facebook-Video-Download-API) as fallback for Facebook videos when yt-dlp fails
- **Video preview**: See title, thumbnail, duration before downloading

## Prerequisites

1. **Python 3.8+**
2. **FFmpeg** – required for merging audio/video streams (DASH format)

### Install FFmpeg

- **Windows**: [Download from ffmpeg.org](https://ffmpeg.org/download.html) or `choco install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

## Installation

```bash
# Clone or navigate to the project
cd video_downloader

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

Then:

1. Paste a video URL (YouTube, Shorts, Facebook, Reels)
2. Select quality
3. Click **Download Video**
4. Click **Save Video** when ready

## Optional: Facebook Video Download API

For Facebook videos, yt-dlp may sometimes fail. You can run the [Facebook Video Download API](https://github.com/sh13y/Facebook-Video-Download-API) locally and use it as a fallback:

```bash
# In another terminal, run the Facebook API
git clone https://github.com/sh13y/Facebook-Video-Download-API.git
cd Facebook-Video-Download-API
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then in the Video Downloader sidebar, enter: `http://localhost:8000`

## Supported URL Formats

| Platform   | Examples |
|-----------|----------|
| YouTube   | `https://www.youtube.com/watch?v=...`, `https://youtu.be/...` |
| Shorts    | `https://www.youtube.com/shorts/...` |
| Facebook  | `https://www.facebook.com/watch/?v=...`, `https://fb.watch/...` |
| Reels     | `https://www.facebook.com/reel/...` |

## Tech Stack

- **Streamlit** – UI
- **yt-dlp** – Video extraction (supports 1000+ sites)
- **FFmpeg** – Audio/video merging
- **requests** – HTTP client

## License

MIT
