import subprocess
import json
import sys
import re
import difflib
from pathlib import Path

# Fix path to find config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\n', ' ')
    return ' '.join(text.split()).strip()

def get_new_content(old_text, new_text):
    if not old_text: return new_text
    if old_text in new_text: return new_text.replace(old_text, "", 1).strip()
    s = difflib.SequenceMatcher(None, old_text, new_text)
    match = s.find_longest_match(0, len(old_text), 0, len(new_text))
    if match.b == 0 and match.size > 5:
        return new_text[match.size:].strip()
    return new_text

def process_vtt(vtt_path):
    content = vtt_path.read_text(encoding='utf-8')
    blocks = re.split(r'\n\s*\n', content)
    raw_stream = []
    last_text = ""

    for block in blocks:
        match = re.search(r'(\d{2}:\d{2}:\d{2}.\d{3}) --> (\d{2}:\d{2}:\d{2}.\d{3})', block)
        if not match: continue
        start_str, end_str = match.groups()
        lines = [l for l in block.splitlines() if '-->' not in l and 'WEBVTT' not in l and l.strip()]
        current_text = clean_text(" ".join(lines))
        if not current_text: continue
        new_part = get_new_content(last_text, current_text)
        if new_part:
            def to_sec(t):
                h, m, s = t.split(':')
                return round(float(h)*3600 + float(m)*60 + float(s), 3)
            raw_stream.append({"start": to_sec(start_str), "end": to_sec(end_str), "text": new_part})
            last_text = current_text

    final_segments = []
    if not raw_stream: return []
    buffer_segment = raw_stream[0]
    for i in range(1, len(raw_stream)):
        nxt = raw_stream[i]
        needs_break = any(char in buffer_segment['text'] for char in '.?!') or len(buffer_segment['text'].split()) > 10
        if not needs_break:
            buffer_segment['text'] += " " + nxt['text']
            buffer_segment['end'] = nxt['end']
        else:
            final_segments.append(buffer_segment)
            buffer_segment = nxt
    final_segments.append(buffer_segment)
    return final_segments

def main():
    if len(sys.argv) < 3: sys.exit(1)
    video_url, outdir = sys.argv[1], Path(sys.argv[2])
    
    print(f"    [Subtitles] Attempting to fetch from YouTube...")
    # Try to download subtitles
    result = subprocess.run([
        "yt-dlp", "--write-auto-subs", "--sub-langs", "en", "--skip-download",
        "--no-playlist", "--quiet", "-o", str(outdir / "sub"), video_url
    ])

    vtt_file = next(outdir.glob("*.vtt"), None)
    if not vtt_file:
        print("    [Subtitles] ❌ No VTT file found on YouTube.")
        sys.exit(1)

    segments = process_vtt(vtt_file)
    if not segments:
        print("    [Subtitles] ❌ Parsed segments are empty.")
        sys.exit(1)

    (outdir / "transcript_timed.json").write_text(json.dumps(segments, indent=2), encoding='utf-8')
    vtt_file.unlink()
    print(f"    [Subtitles] ✔ Successfully saved {len(segments)} timed segments.")
    sys.exit(0)

if __name__ == "__main__":
    main()
