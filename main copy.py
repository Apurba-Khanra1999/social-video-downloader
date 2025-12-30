import io
import re
from urllib.parse import urlparse
import requests
import streamlit as st
from yt_dlp import YoutubeDL
import tempfile
import os

st.set_page_config(page_title="Social Video Downloader", page_icon="🎬", layout="centered")
st.markdown(
    """
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3685660158116656" crossorigin="anonymous"></script>
    """,
    unsafe_allow_html=True,
)

def is_instagram_url(u: str) -> bool:
    try:
        p = urlparse(u.strip())
        if not p.scheme.startswith("http"):
            return False
        if not (p.netloc.endswith("instagram.com")):
            return False
        path = p.path.rstrip("/")
        return any(path.startswith(f"/{seg}") for seg in ("p", "reel", "tv"))
    except Exception:
        return False

def is_facebook_url(u: str) -> bool:
    try:
        p = urlparse(u.strip())
        if not p.scheme.startswith("http"):
            return False
        host_ok = p.netloc.endswith("facebook.com") or p.netloc.endswith("fb.watch")
        if not host_ok:
            return False
        path = p.path.rstrip("/")
        return ("/videos/" in path) or path.startswith("/watch") or "/reel/" in path or path.startswith("/reel")
    except Exception:
        return False
def is_youtube_url(u: str) -> bool:
    try:
        p = urlparse(u.strip())
        if not p.scheme.startswith("http"):
            return False
        host_ok = p.netloc.endswith("youtube.com") or p.netloc.endswith("youtu.be")
        if not host_ok:
            return False
        path = p.path.rstrip("/")
        return (path.startswith("/watch") or path.startswith("/shorts") or path.startswith("/embed") or (p.netloc.endswith("youtu.be") and path.strip("/") != ""))
    except Exception:
        return False

def extract_videos(u: str):
    ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": False, "geo_bypass": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(u, download=False)
    items = info.get("entries") or [info]
    videos = []
    for item in items:
        fmts = item.get("formats") or []
        clean_formats = []
        best = None
        for f in fmts:
            if not f.get("url"):
                continue
            ext = (f.get("ext") or "").lower()
            mt = (f.get("mime_type") or "").lower()
            if "mp4" not in ext and "mp4" not in mt:
                continue
            h = f.get("height") or 0
            t = f.get("tbr") or 0
            if best is None or (h, t) > ((best.get("height") or 0), (best.get("tbr") or 0)):
                best = f
        for f in fmts:
            if not f.get("url"):
                continue
            clean_formats.append({
                "url": f.get("url"),
                "format_id": f.get("format_id"),
                "ext": (f.get("ext") or "").lower(),
                "height": f.get("height"),
                "width": f.get("width"),
                "tbr": f.get("tbr"),
                "fps": f.get("fps"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
                "format_note": f.get("format_note"),
                "audio_channels": f.get("audio_channels"),
                "container": f.get("container"),
                "mime_type": f.get("mime_type"),
                "protocol": f.get("protocol"),
            })
        if best is None and item.get("url"):
            best = {"url": item["url"], "ext": item.get("ext") or "mp4", "height": item.get("height")}
        if best:
            title = item.get("title") or item.get("id") or "video"
            safe = re.sub(r"[\\/:*?\"<>|]+", "-", title)
            videos.append({
                "title": title,
                "url": best["url"],
                "filename": f"{safe}.mp4",
                "thumb": item.get("thumbnail"),
                "height": best.get("height") or item.get("height"),
                "width": best.get("width") or item.get("width"),
                "tbr": best.get("tbr"),
                "duration": item.get("duration"),
                "uploader": item.get("uploader") or item.get("channel") or item.get("creator"),
                "uploader_id": item.get("uploader_id"),
                "view_count": item.get("view_count"),
                "like_count": item.get("like_count"),
                "comment_count": item.get("comment_count"),
                "upload_date": item.get("upload_date"),
                "tags": item.get("tags"),
                "description": item.get("description"),
                "webpage_url": item.get("webpage_url") or item.get("original_url"),
                "source": item.get("extractor"),
                "ext": best.get("ext"),
                "fps": best.get("fps"),
                "vcodec": best.get("vcodec"),
                "acodec": best.get("acodec"),
                "filesize": best.get("filesize") or best.get("filesize_approx"),
                "format_note": best.get("format_note"),
                "formats_full": clean_formats,
            })
    return videos

def download_buffer(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    r = requests.get(url, stream=True, timeout=60, headers=headers)
    total = int(r.headers.get("content-length") or 0)
    buf = io.BytesIO()
    prog = st.progress(0)
    downloaded = 0
    for chunk in r.iter_content(chunk_size=8192):
        if not chunk:
            continue
        buf.write(chunk)
        downloaded += len(chunk)
        if total:
            prog.progress(min(downloaded / total, 1.0))
    prog.progress(1.0)
    buf.seek(0)
    return buf
def format_duration(seconds):
    try:
        s = int(seconds or 0)
    except Exception:
        s = 0
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"
def format_filesize(b):
    try:
        n = float(b or 0)
    except Exception:
        n = 0.0
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    return f"{n:.2f} {units[i]}"
def format_date(d):
    s = str(d or "")
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else s
def download_via_ytdlp(u: str, format_id: str) -> io.BytesIO:
    tmpdir = tempfile.mkdtemp()
    outtmpl = os.path.join(tmpdir, "download.%(ext)s")
    ydl_opts = {"quiet": True, "format": format_id, "outtmpl": outtmpl, "noplaylist": True}
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([u])
    files = os.listdir(tmpdir)
    if not files:
        raise RuntimeError("Download failed")
    path = os.path.join(tmpdir, files[0])
    with open(path, "rb") as f:
        data = f.read()
    try:
        os.remove(path)
        os.rmdir(tmpdir)
    except Exception:
        pass
    return io.BytesIO(data)

st.sidebar.title("Social Downloader")
platform = st.sidebar.radio("Choose platform", ["Instagram", "Facebook", "YouTube"], index=0)
st.sidebar.divider()
st.sidebar.caption("Developed by Apurba Khanra")

st.title("🎬 Social Video Downloader")
if platform == "Instagram":
    st.caption("Paste a link to a public Instagram video or reel")
elif platform == "Facebook":
    st.caption("Paste a link to a public Facebook video")
else:
    st.caption("Paste a link to a YouTube video")

if "videos" not in st.session_state:
    st.session_state.videos = None
if "last_url" not in st.session_state:
    st.session_state.last_url = ""

with st.form("fetch_form"):
    if platform == "Instagram":
        url = st.text_input("Instagram link", placeholder="https://www.instagram.com/reel/...", value=st.session_state.last_url)
    elif platform == "Facebook":
        url = st.text_input("Facebook link", placeholder="https://www.facebook.com/username/videos/...", value=st.session_state.last_url)
    else:
        url = st.text_input("YouTube link", placeholder="https://www.youtube.com/watch?v=...", value=st.session_state.last_url)
    fetch = st.form_submit_button("Fetch")
clear = st.button("Clear")

if clear:
    st.session_state.videos = None
    st.session_state.last_url = ""

if fetch:
    if not url:
        st.error("Enter a valid URL")
        st.stop()
    if platform == "Instagram" and not is_instagram_url(url.strip()):
        st.error("Enter a valid Instagram reel/video URL")
        st.stop()
    if platform == "Facebook" and not is_facebook_url(url.strip()):
        st.error("Enter a valid Facebook video URL")
        st.stop()
    if platform == "YouTube" and not is_youtube_url(url.strip()):
        st.error("Enter a valid YouTube video URL")
        st.stop()
    st.session_state.last_url = url.strip()
    with st.spinner("Fetching video"):
        try:
            vids = extract_videos(st.session_state.last_url)
            st.session_state.videos = vids if vids else None
        except Exception as e:
            st.session_state.videos = None
            st.error(f"Failed to fetch: {e}")

if st.session_state.videos:
    titles = [v["title"] for v in st.session_state.videos]
    idx = 0
    if len(titles) > 1:
        idx = st.selectbox("Select item", list(range(len(titles))), format_func=lambda i: titles[i])
    chosen = st.session_state.videos[idx]
    tabs = st.tabs(["Preview"])
    with tabs[0]:
        st.subheader(chosen.get("title") or "Preview")
        c1, c2 = st.columns([3, 2])
        with c1:
            st.video(chosen["url"])
        with c2:
            if platform == "YouTube":
                f_all = chosen.get("formats_full") or []
                type_choice = st.radio("Type", ["Video (with audio)", "Audio only", "Video only"])
                def label_fmt(f):
                    h = f.get("height")
                    hz = f.get("fps")
                    tbr = f.get("tbr")
                    note = f.get("format_note") or ""
                    ext = f.get("ext")
                    base = f"{h}p" if h else "audio"
                    parts = [base, ext]
                    if note:
                        parts.append(note)
                    if hz:
                        parts.append(f"{int(hz)}fps")
                    if tbr:
                        parts.append(f"{int(tbr)}kbps")
                    return " • ".join(parts)
                direct = lambda f: (f.get("protocol") in (None, "http", "https") and f.get("url"))
                va = [f for f in f_all if direct(f) and (f.get("vcodec") or "") != "none" and (f.get("acodec") or "") != "none"]
                ao = [f for f in f_all if direct(f) and (f.get("vcodec") or "") == "none" and (f.get("acodec") or "") != "none"]
                vo = [f for f in f_all if direct(f) and (f.get("vcodec") or "") != "none" and (f.get("acodec") or "") == "none"]
                choices = va if type_choice.startswith("Video (with audio)") else (ao if type_choice.startswith("Audio") else vo)
                idx_sel = 0
                if choices:
                    idx_sel = st.selectbox("Quality", list(range(len(choices))), format_func=lambda i: label_fmt(choices[i]))
                dl = st.button("Download Selected")
                if dl and choices:
                    sel = choices[idx_sel]
                    with st.spinner("Downloading"):
                        fid = sel.get("format_id")
                        if fid:
                            buf = download_via_ytdlp(chosen.get("webpage_url") or chosen["url"], fid)
                        else:
                            buf = download_buffer(sel["url"])
                    ext = sel.get("ext") or "mp4"
                    typ = "audio" if type_choice.startswith("Audio") else "video"
                    if ext == "webm":
                        mime = "audio/webm" if typ == "audio" else "video/webm"
                    elif ext in ("m4a", "mp4"):
                        mime = "audio/mp4" if typ == "audio" else "video/mp4"
                    else:
                        mime = "application/octet-stream"
                    st.success("Ready")
                    st.download_button("Download", buf, file_name=f"{chosen['filename'].rsplit('.',1)[0]}.{ext}", mime=mime)
            else:
                dl = st.button("Download MP4")
                if dl:
                    with st.spinner("Downloading"):
                        buf = download_buffer(chosen["url"])
                    st.success("Ready")
                    st.download_button("Download MP4", buf, file_name=chosen["filename"], mime="video/mp4")
            h = chosen.get("height")
            res = f"{h}p" if h else "Unknown"
            br = f'{int(chosen.get("tbr") or 0)} kbps' if chosen.get("tbr") else "Unknown"
            dur = format_duration(chosen.get("duration"))
            st.caption(f"Resolution: {res}")
            st.caption(f"Bitrate: {br}")
            st.caption(f"Duration: {dur}")
            st.caption(f'Title: {chosen.get("title") or "Unknown"}')
            st.caption(f'Uploader: {chosen.get("uploader") or "Unknown"}')
            
            if chosen.get("thumb"):
                st.image(chosen["thumb"], width=360)
            st.divider()
            more = {
                "File size": format_filesize(chosen.get("filesize")),
                "FPS": chosen.get("fps") or "Unknown",
                "Video codec": chosen.get("vcodec") or "Unknown",
                "Audio codec": chosen.get("acodec") or "Unknown",
                "Format": chosen.get("ext") or "mp4",
                "Format note": chosen.get("format_note") or "Unknown",
                "Uploaded": format_date(chosen.get("upload_date")),
                "Views": chosen.get("view_count") or "Unknown",
                "Likes": chosen.get("like_count") or "Unknown",
                "Comments": chosen.get("comment_count") or "Unknown",
                "Source": chosen.get("source") or "Unknown",
            }
            for k, v in more.items():
                st.caption(f"{k}: {v}")
            if chosen.get("tags"):
                st.caption(f'Tags: {", ".join(chosen.get("tags") or [])}')
            if chosen.get("webpage_url"):
                st.caption(f'Page: {chosen.get("webpage_url")}')
            if chosen.get("description"):
                st.expander("Description").write(chosen.get("description"))
