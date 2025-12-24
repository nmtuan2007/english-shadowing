# ================================================
# FILE: server.py
# ================================================
import json
import re
import subprocess
import sys
import uuid
import os
import threading
import difflib
import urllib.parse
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from pydantic import BaseModel
from openai import OpenAI

# Try importing whisper for scoring
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    print("⚠️ Warning: 'whisper' not found. Scoring will be disabled.")

# --- CONFIGURATION ---
# Force absolute path to avoid CWD confusion
BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / "lessons"
SCRIPTS_DIR = BASE_DIR / "scripts"
SOURCES_FILE = BASE_DIR / "sources.json"
PROGRESS_FILE = BASE_DIR / "progress.json"
VOCAB_FILE = BASE_DIR / "vocab.json"
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

print(f"📂 Server Root: {BASE_DIR}")
print(f"📂 Lessons Dir: {LESSONS_DIR}")

# Import AI settings from config
sys.path.append(str(BASE_DIR))
try:
    from config import AI_API_KEY, AI_BASE_URL, AI_MODEL, WHISPER_MODEL
except ImportError:
    print("⚠️ Config not found. Creating dummy variables.")
    AI_API_KEY, AI_BASE_URL, AI_MODEL, WHISPER_MODEL = "", "", "", "base"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL STATE ---
client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
scorer_model = None

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

class DefineRequest(BaseModel):
    text: str
    context: str

class SaveVocabRequest(BaseModel):
    lesson_id: str
    word: str
    definition: str
    ipa: str
    context: str
    translation: str
    type: str

# --- HELPERS ---
def load_scorer_model():
    """Load Whisper model once for scoring endpoints"""
    global scorer_model
    if HAS_WHISPER and scorer_model is None:
        print(f"🧠 Loading Whisper '{WHISPER_MODEL}' for scoring...")
        try:
            scorer_model = whisper.load_model(WHISPER_MODEL)
            print("✅ Whisper loaded.")
        except Exception as e:
            print(f"❌ Failed to load Whisper: {e}")

def get_progress() -> List[str]:
    if not PROGRESS_FILE.exists(): return []
    try: return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except: return []

def save_progress(progress_list: List[str]):
    PROGRESS_FILE.write_text(json.dumps(progress_list), encoding="utf-8")

def get_vocab_data() -> List[Dict]:
    if not VOCAB_FILE.exists(): return []
    try: return json.loads(VOCAB_FILE.read_text(encoding="utf-8"))
    except: return []

def save_vocab_data(data: List[Dict]):
    VOCAB_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def sanitize_filename(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^\w\s-]', '', name)
    return re.sub(r'[\s_-]+', '_', name).strip('_')[:50]

def run_generation_task(category: str, lesson_id: str):
    print(f"⚡ [Task] Starting generation for {category}/{lesson_id}")
    try:
        (LESSONS_DIR / category / lesson_id).mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_lessons.py"), category, lesson_id],
            check=True
        )
        print(f"✅ [Task] Completed generation for {category}/{lesson_id}")
    except Exception as e:
        print(f"❌ [Task] Error: {e}")

# --- LIFECYCLE ---
@app.on_event("startup")
async def startup_event():
    # Ensure lessons directory exists so StaticFiles mount doesn't fail
    if not LESSONS_DIR.exists():
        print(f"⚠️ Lessons directory not found at {LESSONS_DIR}. Creating it...")
        LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load model in a separate thread
    if HAS_WHISPER:
        threading.Thread(target=load_scorer_model, daemon=True).start()

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
            
            # Check for ANY video file
            has_video = any(lesson_dir.glob("video.*"))
            has_timed = (lesson_dir / "transcript_timed.json").exists()
            has_final = (lesson_dir / "shadowing_final.txt").exists()
            
            lesson["done"] = lid in progress
            lesson["downloaded"] = has_final
            
            if has_final: lesson["status"] = "ready"
            elif has_timed: lesson["status"] = "generating_ai"
            elif has_video: lesson["status"] = "transcribing"
            elif lesson_dir.exists(): lesson["status"] = "downloading"
            else: lesson["status"] = "not_started"
    return sources

@app.post("/api/add-lesson")
def add_lesson(req: AddLessonRequest, background_tasks: BackgroundTasks):
    if "youtube.com" not in req.url and "youtu.be" not in req.url:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s|%(duration)s", "--no-playlist", req.url],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip().split("|")
        title = output[0]
        duration = int(float(output[1])) if len(output) > 1 else 0
        lesson_id = sanitize_filename(title)
    except:
        raise HTTPException(status_code=400, detail="Video not found")

    if not SOURCES_FILE.exists(): SOURCES_FILE.write_text("{}")
    with open(SOURCES_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if req.category not in data: data[req.category] = []
        if not any(l["lesson"] == lesson_id for l in data[req.category]):
            data[req.category].insert(0, {
                "lesson": lesson_id, "title": title, "url": req.url,
                "source": "Custom", "level": "??", "duration": duration
            })
            f.seek(0); json.dump(data, f, indent=2, ensure_ascii=False); f.truncate()
    
    background_tasks.add_task(run_generation_task, req.category, lesson_id)
    return {"status": "queued", "lesson_id": lesson_id}

@app.post("/api/start-lesson")
def start_lesson(req: StartLessonRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_generation_task, req.category, req.lesson_id)
    return {"status": "queued"}

@app.get("/api/lesson/{category}/{lesson_id}")
def get_lesson(category: str, lesson_id: str, request: Request):
    lesson_dir = LESSONS_DIR / category / lesson_id
    path_timed, path_final = lesson_dir / "transcript_timed.json", lesson_dir / "shadowing_final.txt"
    
    # DEBUG: Print exactly what we are looking for
    print(f"🔎 Request for lesson: {category}/{lesson_id}")
    print(f"   Looking in: {lesson_dir}")
    
    if not lesson_dir.exists(): 
        print("   ❌ Directory does not exist")
        return {"status": "not_started"}
        
    # Find actual video filename (could be video.mp4, video.webm, etc)
    video_file = next(lesson_dir.glob("video.*"), None)
    if not video_file:
        print("   ❌ No video.* file found")
        return {"status": "downloading"}

    print(f"   ✅ Found video: {video_file.name}")

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

        # SAFE URL CONSTRUCTION
        base_url = str(request.base_url).rstrip("/")
        # Encode components to handle spaces/special chars safely
        safe_category = urllib.parse.quote(category)
        safe_lesson_id = urllib.parse.quote(lesson_id)
        safe_filename = urllib.parse.quote(video_file.name)
        
        video_url = f"{base_url}/media/{safe_category}/{safe_lesson_id}/{safe_filename}"
        print(f"   🔗 Serving URL: {video_url}")

        return {
            "status": "ready", 
            "transcript": final, 
            "video_url": video_url
        }
    except Exception as e:
        print(f"   ❌ Error loading data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/done")
def toggle_done(req: DoneRequest):
    p = set(get_progress())
    if req.done: p.add(req.lesson_id)
    else: p.discard(req.lesson_id)
    save_progress(list(p))
    return {"status": "success"}

# --- VOCABULARY ROUTES ---
@app.post("/api/define")
def define_word(req: DefineRequest):
    prompt = f"""Explain "{req.text}" in context: "{req.context}". Return JSON: {{"definition": "...", "translation": "...", "ipa": "...", "type": "..."}}"""
    try:
        completion = client.chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.1
        )
        content = completion.choices[0].message.content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI Error")

@app.get("/api/vocab")
def get_vocab(lesson_id: Optional[str] = None):
    data = get_vocab_data()
    if lesson_id: data = [v for v in data if v["lesson_id"] == lesson_id]
    return sorted(data, key=lambda x: x.get("timestamp", 0), reverse=True)

@app.post("/api/vocab")
def save_vocab(req: SaveVocabRequest):
    data = get_vocab_data()
    for item in data:
        if item["word"].lower() == req.word.lower() and item["lesson_id"] == req.lesson_id:
            return {"status": "already_saved", "id": item["id"]}
    import time
    new_item = {**req.dict(), "id": str(uuid.uuid4()), "timestamp": time.time()}
    data.append(new_item)
    save_vocab_data(data)
    return {"status": "success", "data": new_item}

@app.delete("/api/vocab/{vocab_id}")
def delete_vocab(vocab_id: str):
    data = [v for v in get_vocab_data() if v["id"] != vocab_id]
    save_vocab_data(data)
    return {"status": "deleted"}

# --- SCORING ROUTE ---

@app.post("/api/score")
async def score_audio(target_text: str = Form(...), file: UploadFile = File(...)):
    """Transcribe audio and compare with target text"""
    if not HAS_WHISPER or scorer_model is None:
        return {"transcript": "Scoring unavailable (Whisper not loaded)", "score": 0, "status": "error"}

    # Save temp file
    temp_path = TEMP_DIR / f"{uuid.uuid4()}.webm"
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # Transcribe
        result = scorer_model.transcribe(str(temp_path), fp16=False, language="en")
        user_text = result["text"].strip()
        
        # Calculate Similarity
        matcher = difflib.SequenceMatcher(None, target_text.lower(), user_text.lower())
        score = matcher.ratio() * 100
        
        return {
            "status": "success",
            "transcript": user_text,
            "target": target_text,
            "score": round(score, 1)
        }
    except Exception as e:
        print(f"Scoring Error: {e}")
        return {"status": "error", "message": str(e), "score": 0}
    finally:
        if temp_path.exists():
            os.remove(temp_path)

# --- MOUNT STATIC FILES ---
# Ensure directory exists immediately before mounting
if not LESSONS_DIR.exists():
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    
print(f"📡 Mounting /media -> {LESSONS_DIR}")
app.mount("/media", StaticFiles(directory=LESSONS_DIR), name="media")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
