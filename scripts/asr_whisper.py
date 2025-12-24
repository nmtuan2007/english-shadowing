import whisper
import json
import sys
from pathlib import Path

# Fix path to find config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import WHISPER_MODEL

def main():
    if len(sys.argv) < 3: sys.exit(1)
    audio_path = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    
    print(f"    [Whisper] 🎙 Loading model '{WHISPER_MODEL}'...")
    try:
        model = whisper.load_model(WHISPER_MODEL)
        print(f"    [Whisper] ⏳ Transcribing audio (this may take a minute)...")
        result = model.transcribe(str(audio_path), verbose=False)

        segments = []
        for s in result['segments']:
            segments.append({
                "start": round(s['start'], 3),
                "end": round(s['end'], 3),
                "text": s['text'].strip()
            })

        (outdir / "transcript_timed.json").write_text(json.dumps(segments, indent=2), encoding='utf-8')
        print(f"    [Whisper] ✔ Generated {len(segments)} segments.")
        sys.exit(0)
    except Exception as e:
        print(f"    [Whisper] ❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
