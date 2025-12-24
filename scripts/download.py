import sys
import subprocess
from pathlib import Path


def run(cmd: list):
    """Run a command and raise exception on failure."""
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) < 3:
        print("Usage: python download.py <url> <output_dir>")
        sys.exit(1)

    url = sys.argv[1]
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    video_path = outdir / "video.mp4"
    audio_path = outdir / "audio.mp3"

    # Download video
    print(f"  Downloading video: {url}")
    run([
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "-o", str(video_path),
        "--no-playlist",
        url
    ])

    # Extract audio
    print(f"  Extracting audio...")
    run([
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        str(audio_path)
    ])

    print(f"✔ Downloaded: {video_path.name} + {audio_path.name}")


if __name__ == "__main__":
    main()
