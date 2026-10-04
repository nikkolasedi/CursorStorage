"""Download a shared Instagram reel/post and turn it into research material.

Usage:
    python3 manifestatio-opus/compose/fetch_reel.py <instagram-url> <out-dir>

Writes into <out-dir>:
    source.json      uploader, caption, duration, url
    video.mp4        the reel (skipped for photo posts)
    transcript.txt   spoken audio, timestamped
    frames/NN.jpg    one frame every few seconds, for on-screen text and visuals

Requires: pip install yt-dlp faster-whisper ; ffmpeg on PATH.
"""

import json
import subprocess
import sys
from pathlib import Path

import yt_dlp


def fetch(url, out):
    out.mkdir(parents=True, exist_ok=True)
    opts = {
        "quiet": True,
        "format": "b",
        "outtmpl": str(out / "video.%(ext)s"),
        "writethumbnail": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    meta = {
        "url": url,
        "uploader": info.get("uploader") or info.get("channel"),
        "title": info.get("title"),
        "caption": info.get("description"),
        "duration": info.get("duration"),
        "timestamp": info.get("timestamp"),
    }
    (out / "source.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def frames(video, out, every=4):
    fdir = out / "frames"
    fdir.mkdir(exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(video),
         "-vf", f"fps=1/{every},scale=540:-1", str(fdir / "%02d.jpg")],
        check=True,
    )


def transcribe(video, out, model_size="small"):
    import numpy as np
    from faster_whisper import WhisperModel

    # faster-whisper's own decoder breaks on some PyAV versions; ffmpeg is reliable.
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-f", "f32le",
         "-ac", "1", "-ar", "16000", "-"],
        check=True, capture_output=True,
    ).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio, vad_filter=True)
    lines = [f"# language: {info.language}"]
    for s in segments:
        lines.append(f"[{s.start:6.1f}-{s.end:6.1f}] {s.text.strip()}")
    (out / "transcript.txt").write_text("\n".join(lines) + "\n")


def main():
    url, out = sys.argv[1], Path(sys.argv[2])
    fetch(url, out)
    video = next(iter(out.glob("video.mp4")), None)
    if video:
        frames(video, out)
        transcribe(video, out)
    print(out)


if __name__ == "__main__":
    main()
