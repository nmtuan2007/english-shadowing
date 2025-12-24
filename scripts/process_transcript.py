import json
import sys
import time
import re
from pathlib import Path
from openai import OpenAI

# Fix path to find config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import AI_MODEL, AI_API_KEY, AI_BASE_URL

def process_chunk(client, chunk_lines):
    system_message = "You are a data conversion engine. Output ONLY structured text in format: [index] | EN | VI | GUIDE"
    user_prompt = f"Process these lines for shadowing:\n{chunk_lines}"
    
    for i in range(3):
        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "system", "content": system_message}, {"role": "user", "content": user_prompt}],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"      ⚠️ AI Attempt {i+1} failed: {e}")
            time.sleep(5)
    return ""

def main():
    if len(sys.argv) < 3: sys.exit(1)
    outdir = Path(sys.argv[2])
    timed_json_path = outdir / "transcript_timed.json"
    
    if not timed_json_path.exists():
        print(f"    [AI] ❌ Aborting: {timed_json_path.name} not found.")
        sys.exit(1)

    segments = json.loads(timed_json_path.read_text(encoding='utf-8'))
    client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    
    full_results = []
    chunk_size = 10
    
    print(f"    [AI] 🤖 Processing {len(segments)} segments...")
    for i in range(0, len(segments), chunk_size):
        chunk = segments[i:i + chunk_size]
        chunk_lines = "\n".join([f"[{i+j}] {s['text']}" for j, s in enumerate(chunk)])
        raw_result = process_chunk(client, chunk_lines)
        
        for line in raw_result.splitlines():
            if re.match(r"^\[\d+\]", line.strip()) and "|" in line:
                full_results.append(line.strip())

    (outdir / "shadowing_final.txt").write_text("\n".join(full_results), encoding='utf-8')
    print(f"    [AI] ✅ Saved {len(full_results)} processed lines.")
    sys.exit(0)

if __name__ == "__main__":
    main()
