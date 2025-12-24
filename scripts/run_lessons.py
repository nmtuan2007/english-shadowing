import subprocess
import sys
import json
from pathlib import Path

# Ensure we can import config.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SCRIPTS_DIR, LESSONS_DIR, SOURCES_FILE

def run_script(script_name, args):
    """Runs a script using the current python executable to ensure environment match."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + args
    return subprocess.run(cmd)

def process_lesson(category: str, lesson: dict):
    """The core logic to process one lesson."""
    lesson_id = lesson["lesson"]
    url = lesson["url"]
    lesson_dir = LESSONS_DIR / category / lesson_id
    lesson_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n▶ [{category.upper()}] {lesson['title']}")
    
    video_path = lesson_dir / "video.mp4"
    audio_path = lesson_dir / "audio.mp3"
    timed_json = lesson_dir / "transcript_timed.json"
    final_txt = lesson_dir / "shadowing_final.txt"

    if final_txt.exists():
        print("  ✔ Already completed.")
        return True

    # 1. Download
    if not video_path.exists():
        print("  1️⃣ Downloading...")
        if run_script("download.py", [url, str(lesson_dir)]).returncode != 0:
            return False

    # 2. Transcribe (Timed)
    if not timed_json.exists():
        print("  2️⃣ Extracting timestamps...")
        # Try YouTube first
        if run_script("get_transcript.py", [url, str(lesson_dir)]).returncode != 0:
            print("  ⚠️ YouTube subs failed. Trying Whisper (local fallback)...")
            # Try Whisper fallback
            if run_script("asr_whisper.py", [str(audio_path), str(lesson_dir)]).returncode != 0:
                print("  ❌ All transcription methods failed.")
                return False

    # 3. AI Process (EN/VI/GUIDE Sync)
    if not final_txt.exists():
        print("  3️⃣ Generating shadowing materials...")
        # Passing dummy path for arg1 as script now looks directly for transcript_timed.json in outdir
        if run_script("process_transcript.py", ["unused", str(lesson_dir)]).returncode != 0:
            return False

    print("  ✨ Lesson Ready!")
    return True

# --- FUNCTIONS REQUIRED BY APP.PY ---

def load_sources():
    """Loads the sources.json file."""
    if not SOURCES_FILE.exists():
        print(f"❌ {SOURCES_FILE} not found.")
        sys.exit(1)
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def run_all(sources):
    """Processes every lesson in every category."""
    for cat in sources:
        run_category(cat, sources)

def run_category(category, sources):
    """Processes all lessons in a specific category."""
    if category not in sources:
        print(f"❌ Category {category} not found in sources.")
        return
    
    print(f"\n{'='*60}")
    print(f" PROCESSING CATEGORY: {category.upper()}")
    print(f"{'='*60}")
    
    for lesson in sources[category]:
        process_lesson(category, lesson)

def run_single_lesson(category, lesson_id, sources):
    """Processes one specific lesson."""
    if category not in sources:
        print(f"❌ Category {category} not found.")
        return False
        
    lesson = next((l for l in sources[category] if l["lesson"] == lesson_id), None)
    if not lesson:
        print(f"❌ Lesson {lesson_id} not found in {category}.")
        return False
        
    return process_lesson(category, lesson)

if __name__ == "__main__":
    # Internal CLI for direct script testing
    sources_data = load_sources()
    if len(sys.argv) < 2:
        run_all(sources_data)
    elif len(sys.argv) == 2:
        run_category(sys.argv[1], sources_data)
    else:
        run_single_lesson(sys.argv[1], sys.argv[2], sources_data)
