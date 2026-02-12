import streamlit as st
import yt_dlp
import os
from pathlib import Path
import tempfile

st.set_page_config(page_title="YouTube MP3 Downloader", page_icon="🎵", layout="centered")

# --------------------------
# TEMP DIRECTORY
# --------------------------
TEMP_DIR = Path(tempfile.gettempdir()) / "youtube_mp3_downloads"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------
# SESSION STATE INIT
# --------------------------
if "urls" not in st.session_state:
    st.session_state.urls = [""]

if "videos" not in st.session_state:
    st.session_state.videos = []

# --------------------------
# FUNCTIONS
# --------------------------
def add_field():
    st.session_state.urls.append("")

def remove_field(index):
    if len(st.session_state.urls) > 1:
        st.session_state.urls.pop(index)
    else:
        st.session_state.urls = [""]

    for key in list(st.session_state.keys()):
        if key.startswith("url_"):
            del st.session_state[key]

    st.rerun()

def get_video_info(url):
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# ✅ ฟังก์ชันดาวน์โหลดที่ถูกต้อง
def download_audio(url):

    progress = st.progress(0)

    def hook(d):
        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            if total:
                percent = int(min(downloaded / total * 100, 100))
                progress.progress(percent)
        elif d["status"] == "finished":
            progress.progress(100)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(TEMP_DIR / "%(title)s_%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }],
        "progress_hooks": [hook],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        # ✅ วิธีดึง path ที่ถูกต้อง
        file_path = ydl.prepare_filename(info)
        file_path = Path(file_path).with_suffix(".mp3")

    return file_path


# --------------------------
# UI
# --------------------------
st.title("🎵 YouTube MP3 Downloader")
st.subheader("🔗 วางลิงก์ YouTube")

for i in range(len(st.session_state.urls)):
    col1, col2 = st.columns([8,1])

    with col1:
        st.session_state.urls[i] = st.text_input(
            f"Link {i+1}",
            value=st.session_state.urls[i],
            key=f"url_{i}"
        )

    with col2:
        if st.button("❌", key=f"remove_{i}"):
            remove_field(i)

st.button("➕ เพิ่มช่อง", on_click=add_field)

# --------------------------
# CHECK BUTTON
# --------------------------
if st.button("🔍 ตรวจสอบลิงก์ทั้งหมด"):

    st.session_state.videos = []

    for url in st.session_state.urls:
        if url.strip():
            try:
                with st.spinner("กำลังดึงข้อมูล..."):
                    info = get_video_info(url)

                st.session_state.videos.append({
                    "info": info,
                    "url": url
                })

            except Exception:
                st.error(f"❌ ลิงก์มีปัญหา: {url}")

# --------------------------
# SHOW VIDEO CARDS
# --------------------------
for idx, item in enumerate(st.session_state.videos):

    info = item["info"]
    url = item["url"]

    duration = info.get("duration", 0)
    minutes = duration // 60
    seconds = duration % 60

    st.markdown(f"""
    <div style="background:#1e1e1e;padding:20px;border-radius:15px;margin-bottom:20px;">
        <img src="{info.get('thumbnail')}" width="100%" style="border-radius:10px;">
        <h4 style="color:white;margin-top:10px;">{info.get('title')}</h4>
        <p style="color:#b3b3b3;">👤 {info.get('uploader')}</p>
        <p style="color:#b3b3b3;">⏱ {minutes}:{seconds:02d}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎧 ดาวน์โหลด MP3", key=f"dl_btn_{idx}"):

        try:
            file_path = download_audio(url)

            if file_path.exists():
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()

                st.download_button(
                    label="⬇️ ดาวน์โหลดไฟล์",
                    data=audio_bytes,
                    file_name=file_path.name,
                    mime="audio/mp3",
                    key=f"download_{idx}"
                )

                os.remove(file_path)

            else:
                st.error("ไม่พบไฟล์ที่ดาวน์โหลด")

        except Exception as e:
            st.error("❌ ดาวน์โหลดไม่สำเร็จ")
            st.code(str(e))
