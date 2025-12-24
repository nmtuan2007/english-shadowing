# ================================================
# FILE: server.py
# ================================================
import json
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / "lessons"
SCRIPTS_DIR = BASE_DIR / "scripts"
SOURCES_FILE = BASE_DIR / "sources.json"
PROGRESS_FILE = BASE_DIR / "progress.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class DoneRequest(BaseModel):
    lesson_id: str
    done: bool

class AddLessonRequest(BaseModel):
    url: str
    category: str = "custom"

class StartLessonRequest(BaseModel):
    category: str
    lesson_id: str

# --- HELPERS ---
def get_progress() -> List[str]:
    if not PROGRESS_FILE.exists(): return []
    try: return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except: return []

def save_progress(progress_list: List[str]):
    PROGRESS_FILE.write_text(json.dumps(progress_list), encoding="utf-8")

def sanitize_filename(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^\w\s-]', '', name)
    return re.sub(r'[\s_-]+', '_', name).strip('_')[:50]

def run_generation_task(category: str, lesson_id: str):
    """Runs the run_lessons.py script in background"""
    print(f"⚡ [Task] Starting generation for {category}/{lesson_id}")
    try:
        # Create directory immediately to mark as 'processing' (downloading)
        (LESSONS_DIR / category / lesson_id).mkdir(parents=True, exist_ok=True)
        
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_lessons.py"), category, lesson_id],
            check=True
        )
        print(f"✅ [Task] Completed generation for {category}/{lesson_id}")
    except Exception as e:
        print(f"❌ [Task] Error: {e}")

# --- ROUTES ---

@app.get("/api/lessons")
def list_lessons():
    if not SOURCES_FILE.exists(): return {}
    try: sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    except: return {}

    progress = get_progress()
    
    for category in sources:
        for lesson in sources[category]:
            lid = lesson["lesson"]
            lesson_dir = LESSONS_DIR / category / lid
            
            # Check Files
            has_video = (lesson_dir / "video.mp4").exists()
            has_timed = (lesson_dir / "transcript_timed.json").exists()
            has_final = (lesson_dir / "shadowing_final.txt").exists()
            
            lesson["done"] = lid in progress
            lesson["downloaded"] = has_final
            
            # Determine Status
            if has_final:
                lesson["status"] = "ready"
            elif has_timed:
                lesson["status"] = "generating_ai" # Video & Timings done, AI running
            elif has_video:
                lesson["status"] = "transcribing" # Video done, waiting for timings
            elif lesson_dir.exists():
                lesson["status"] = "downloading" # Folder exists, but no video yet
            else:
                lesson["status"] = "not_started" # Nothing exists

    return sources

@app.post("/api/add-lesson")
def add_lesson(req: AddLessonRequest, background_tasks: BackgroundTasks):
    if "youtube.com" not in req.url and "youtu.be" not in req.url:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        # Fetch metadata
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s|%(duration)s", "--no-playlist", req.url],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip().split("|")
        title = output[0]
        duration = int(float(output[1])) if len(output) > 1 else 0
        lesson_id = sanitize_filename(title)
        
    except Exception:
        raise HTTPException(status_code=400, detail="Video not found")

    # Update sources
    if not SOURCES_FILE.exists(): SOURCES_FILE.write_text("{}")
    with open(SOURCES_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if req.category not in data: data[req.category] = []
        
        exists = any(l["lesson"] == lesson_id for l in data[req.category])
        if not exists:
            data[req.category].insert(0, {
                "lesson": lesson_id, "title": title, "url": req.url,
                "source": "Custom", "level": "??", "duration": duration
            })
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()
    
    # Trigger
    background_tasks.add_task(run_generation_task, req.category, lesson_id)
    return {"status": "queued", "lesson_id": lesson_id}

@app.post("/api/start-lesson")
def start_lesson(req: StartLessonRequest, background_tasks: BackgroundTasks):
    """Manually trigger download/generation for an existing lesson"""
    background_tasks.add_task(run_generation_task, req.category, req.lesson_id)
    return {"status": "queued", "message": f"Started processing {req.lesson_id}"}

@app.get("/api/lesson/{category}/{lesson_id}")
def get_lesson(category: str, lesson_id: str):
    lesson_dir = LESSONS_DIR / category / lesson_id
    path_timed = lesson_dir / "transcript_timed.json"
    path_final = lesson_dir / "shadowing_final.txt"
    
    # Granular Status for the Practice Page
    if not lesson_dir.exists(): return {"status": "not_started"}
    if not (lesson_dir / "video.mp4").exists(): return {"status": "downloading"}
    if not path_timed.exists(): return {"status": "transcribing"}
    if not path_final.exists(): return {"status": "generating_ai"}
    
    try:
        segments = json.loads(path_timed.read_text(encoding="utf-8"))
        ai_content = path_final.read_text(encoding="utf-8")
        
        processed = {}
        for line in ai_content.splitlines():
            parts = line.split("|")
            if len(parts) >= 3:
                m = re.search(r"\[(\d+)\]", parts[0])
                if m: processed[int(m.group(1))] = {"vi": parts[2].strip(), "guide": parts[3].strip() if len(parts)>3 else ""}

        final = []
        for i, s in enumerate(segments):
            extra = processed.get(i, {"vi": "...", "guide": ""})
            final.append({**s, "id": i, "en": s["text"], "vi": extra["vi"], "guide": extra["guide"]})

        return {
            "status": "ready",
            "transcript": final,
            "video_url": f"http://localhost:8000/media/{category}/{lesson_id}/video.mp4"
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/done")
def toggle_done(req: DoneRequest):
    p = set(get_progress())
    if req.done: p.add(req.lesson_id)
    else: p.discard(req.lesson_id)
    save_progress(list(p))
    return {"status": "success"}

if LESSONS_DIR.exists():
    app.mount("/media", StaticFiles(directory=LESSONS_DIR), name="media")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
