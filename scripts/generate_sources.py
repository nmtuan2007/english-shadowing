import json
import subprocess
import re
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Fallback for imports if config is missing
try:
    from config import (
        CATEGORIES,
        SOURCES_FILE,
        MIN_DURATION,
        MAX_DURATION,
        VIDEOS_PER_CATEGORY
    )
except ImportError:
    CATEGORIES = {}
    SOURCES_FILE = "sources.json"
    MIN_DURATION = 30
    MAX_DURATION = 600
    VIDEOS_PER_CATEGORY = 5


def sanitize_title(title: str) -> str:
    """Convert video title to a valid folder name."""
    title = title.lower()
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[\s_-]+', '_', title)
    title = title.strip('_')
    return title[:50]


def get_video_metadata(channel_url: str, limit: int) -> list:
    """
    Fetch video metadata with actual durations.
    Removes --flat-playlist to ensure durations are not 'NA'.
    """
    # 1. URL HANDLING: Target the /videos tab
    clean_url = channel_url.split('?')[0].rstrip('/')
    if "/channel/" in clean_url or "/@" in clean_url:
        if not clean_url.endswith("/videos"):
            clean_url = f"{clean_url}/videos"

    print(f"  📥 Extracting metadata from {clean_url}...")

    # 2. SUBPROCESS: 
    # We remove --flat-playlist so yt-dlp fetches real durations.
    # We use --playlist-items to limit it to the most recent videos so it stays fast.
    fetch_limit = limit * 3
    result = subprocess.run(
        [
            "yt-dlp",
            "--playlist-items", f"1-{fetch_limit}",
            "--print", "%(id)s|%(duration)s|%(title)s",
            "--no-warnings",
            "--ignore-errors",
            "--quiet",
            "--no-check-certificate",
            clean_url
        ],
        capture_output=True,
        text=False # Keep as bytes to prevent Windows encoding crashes
    )

    if not result.stdout:
        return []
        
    # 3. DECODING: Manual decode with 'replace' to handle special chars like '’'
    output_text = result.stdout.decode('utf-8', errors='replace')
    
    entries = []
    for line in output_text.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
            
        try:
            parts = line.split('|', 2)
            if len(parts) == 3:
                vid_id, dur_raw, title = parts
                
                # If duration is 'NA' or empty, it will be 0
                try:
                    duration = int(dur_raw) if dur_raw != 'NA' else 0
                except:
                    duration = 0

                entries.append({
                    "id": vid_id,
                    "title": title,
                    "duration": duration
                })
        except Exception:
            continue

    return entries


def filter_videos(entries: list, source_name: str, level: str, limit: int) -> list:
    """Filter videos by duration."""
    filtered = []

    for entry in entries:
        if len(filtered) >= limit:
            break

        video_id = entry.get("id")
        title = entry.get("title", "")
        duration = entry.get("duration", 0)

        if not video_id:
            continue

        # Print a clean version of the title to the console
        display_title = title.encode('ascii', 'ignore').decode('ascii')[:45]
        print(f"  Checking: {display_title}...")

        if duration == 0:
            print(f"    ⚠ Could not determine duration (Skipping)")
            continue

        if duration < MIN_DURATION:
            print(f"    ⏭ Too short ({duration}s < {MIN_DURATION}s)")
            continue

        if duration > MAX_DURATION:
            print(f"    ⏭ Too long ({duration}s > {MAX_DURATION}s)")
            continue

        print(f"    ✔ Valid ({duration}s)")

        filtered.append({
            "lesson": sanitize_title(title),
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "source": source_name,
            "level": level,
            "duration": duration
        })

    return filtered


def generate_sources() -> dict:
    """Generate sources for all categories."""
    sources = {}

    for category, config in CATEGORIES.items():
        print(f"\n{'='*50}")
        print(f"📁 Category: {category.upper()}")
        print(f"{'='*50}")

        category_videos = []
        level = config.get("level", "unknown")
        videos_needed = VIDEOS_PER_CATEGORY

        for source in config.get("sources", []):
            if len(category_videos) >= videos_needed:
                break

            source_name = source["name"]
            source_url = source["url"]

            print(f"\n🔍 Fetching from: {source_name}")
            
            # Fetch metadata (now without --flat-playlist for accuracy)
            entries = get_video_metadata(source_url, videos_needed)

            if not entries:
                print(f"  ⚠ No videos found. Try updating yt-dlp (pip install -U yt-dlp)")
                continue

            remaining = videos_needed - len(category_videos)
            filtered = filter_videos(entries, source_name, level, remaining)
            category_videos.extend(filtered)

        # Remove duplicates
        seen = set()
        unique_videos = []
        for video in category_videos:
            if video["lesson"] not in seen:
                seen.add(video["lesson"])
                unique_videos.append(video)

        sources[category] = unique_videos[:videos_needed]
        print(f"\n✅ {category}: {len(sources[category])} videos collected")

    return sources


def save_sources(sources: dict):
    """Save sources to JSON file."""
    try:
        with open(SOURCES_FILE, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Sources saved to: {SOURCES_FILE}")
    except Exception as e:
        print(f"\n❌ Error saving file: {e}")


def main():
    print("🚀 Generating sources.json...")
    print(f"   Duration filter: {MIN_DURATION}s - {MAX_DURATION}s")
    print(f"   Target: {VIDEOS_PER_CATEGORY} videos per category")

    sources = generate_sources()
    if sources:
        save_sources(sources)

    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    total = 0
    for category, videos in sources.items():
        count = len(videos)
        total += count
        print(f"   {category.ljust(15)}: {count} videos")
    print(f"\n   Total: {total} videos")


if __name__ == "__main__":
    main()
