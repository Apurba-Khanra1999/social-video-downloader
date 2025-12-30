# Social Video Downloader (Streamlit)

A simple, beautiful Streamlit app to preview and download videos from Instagram, Facebook, and YouTube. It uses yt-dlp under the hood to extract streams and lets you choose quality for YouTube (video with audio, audio only, or video only).

## Features

- Instagram and Facebook video download with preview
- YouTube support with type selection:
  - Video (with audio)
  - Audio only
  - Video only
- Organized preview tab with:
  - Video player (left) and details + thumbnail + download (right)
  - Resolution, bitrate, duration, codecs, file size, upload date, views, likes, comments, tags, page URL, description
- Default Streamlit light theme, clean native components
- Streaming download with progress and a final download button

## Requirements

- Python 3.9+
- Dependencies:
  - streamlit
  - yt-dlp
  - requests

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python -m streamlit run main.py
```

If your shell does not recognize `streamlit`, prefer the module form shown above.

## Usage

1. Open the app (usually at http://localhost:8501/).
2. In the sidebar, select a platform: Instagram, Facebook, or YouTube.
3. Paste a public video URL and click Fetch.
4. After fetching:
   - Instagram/Facebook: preview shows the video, details, and a Download MP4 button
   - YouTube:
     - Choose Type: Video (with audio), Audio only, or Video only
     - Choose Quality from the available list
     - Click Download Selected

## Notes

- Public posts work out-of-the-box. Private or age-restricted content may require authenticated cookies and can fail without them.
- On YouTube:
  - Lower resolution formats are often progressive (video+audio in one file)
  - Higher resolutions are commonly video-only; choose “Video only” if you want the raw track, or ask for muxing support (see below)

## Muxing (Optional Enhancement)

If you want the highest-resolution video merged with the best audio into a single MP4, this can be added using yt-dlp’s format selection and post-processing. Open an issue or request enhancement and we’ll wire it up.

## Troubleshooting

- “Enter a valid URL”: Ensure the URL is correct and belongs to the selected platform.
- “Failed to fetch”: Network issues, rate limits, private posts, or site changes can cause extraction to fail. Try again or switch networks.
- Streamlit not found: Use `python -m streamlit run main.py`.
- yt-dlp CLI warning: You may see a PATH warning for `yt-dlp.exe`; it’s fine when using the Python module.

## Security and Terms

- Only download content you own or have permission to download.
- Respect platform Terms of Service and local laws.
- Do not share private or sensitive tokens/secrets.

## Credits

Developed by Apurba Khanra

## Code References

- Main app: [main.py](file:///d:/python/video-downloader/main.py)
- Dependencies: [requirements.txt](file:///d:/python/video-downloader/requirements.txt)
