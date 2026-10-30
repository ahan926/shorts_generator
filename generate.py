import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


from config import (
    OUTPUT_DIR,
    CACHE_DIR,
    MUSIC_DIR,
    DEFAULT_VOICE,
    BASE_DIR,
    DEFAULT_CTA
)
from tts_engine import generate_voiceover
from subtitles import generate_ass_subtitles
from stock_media import get_visual_for_segment, reset_used_media
from compositor import assemble_short_video
from audio_ambient import generate_ambient_track

def compute_sentence_durations(
    text: str,
    words: List[Dict[str, Any]],
    total_duration: float,
    expected_segments: int
) -> Optional[List[float]]:
    """
    Calculates the exact spoken duration of each sentence based on word timestamps,
    so that visual cuts happen right on sentence boundaries.
    """
    raw_sentences = [s.strip() for s in re.split(r'[\.\!\?]+', text) if s.strip()]
    if not raw_sentences or not words:
        return None
    
    durations = []
    w_idx = 0
    prev_time = 0.0
    
    for sent in raw_sentences:
        tokens = re.findall(r'\b[A-Za-z0-9]+\b', sent)
        if not tokens:
            continue
        last_word = tokens[-1].lower()
        
        match_idx = None
        for idx in range(w_idx, len(words)):
            w_clean = re.sub(r'[^A-Za-z0-9]', '', words[idx]['word'].lower())
            if w_clean == last_word or w_clean.endswith(last_word):
                match_idx = idx
                break
                
        if match_idx is not None:
            end_time = words[match_idx]['end']
            w_idx = match_idx + 1
        else:
            end_time = prev_time + (total_duration / len(raw_sentences))
            
        dur = max(1.5, end_time - prev_time)
        durations.append(dur)
        prev_time = end_time

    if len(durations) == expected_segments:
        diff = total_duration - sum(durations)
        durations[-1] = max(1.5, durations[-1] + diff)
        return [round(d, 3) for d in durations]
        
    return None

def ensure_background_music() -> Path:
    """Ensures a royalty-free ambient background audio file exists."""
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    if music_files:
        return music_files[0]
        
    ambient_wav = MUSIC_DIR / "ambient_pad.wav"
    print("[Audio] Generating 100% royalty-free procedural ambient soundtrack...")
    generate_ambient_track(ambient_wav, duration_sec=70)
    return ambient_wav

def process_short(
    script_id: str,
    text: str,
    keywords: List[str],
    title: Optional[str] = None,
    description: Optional[str] = None,
    voice: str = DEFAULT_VOICE,
    append_cta: bool = True
) -> Path:
    """End-to-end pipeline to generate a single Short."""
    print(f"\n==================================================")
    print(f"🎬 Generating Short: '{script_id}'")
    print(f"==================================================")
    
    # Reset used media for this Short so all segments are unique within the video
    reset_used_media()
    
    # Automatically append channel subscription CTA if not already present
    text = text.strip()
    if append_cta and DEFAULT_CTA and not text.endswith(DEFAULT_CTA):
        if not text.endswith((".", "!", "?")):
            text += "."
        text += f" {DEFAULT_CTA}"

    
    start_time = time.time()
    work_dir = CACHE_DIR / script_id
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Background Music
    bg_music = ensure_background_music()
    
    # 2. Text to Speech
    print("🗣️  Step 1/4: Synthesizing voiceover with Edge-TTS...")
    audio_path = work_dir / "voiceover.mp3"
    _, words, duration = generate_voiceover(text, audio_path, voice=voice)
    print(f"   Audio generated: {duration:.1f}s ({len(words)} words)")
    
    # 3. Subtitles
    print("📝 Step 2/4: Generating dynamic karaoke ASS subtitles...")
    sub_path = work_dir / "subtitles.ass"
    generate_ass_subtitles(words, sub_path, words_per_phrase=3)
    
    # 4. Sentence-Aligned Segment Durations
    segment_durations = compute_sentence_durations(text, words, duration, expected_segments=len(keywords))
    if segment_durations:
        print(f"   ⏱️  Aligned {len(segment_durations)} visual scenes to spoken explanation sentences:")
        for idx, dur in enumerate(segment_durations):
            print(f"      Scene {idx+1} ({dur:.2f}s): '{keywords[idx]}'")
    
    # 5. Visual Media
    print(f"🖼️  Step 3/4: Fetching {len(keywords)} detailed explanation visuals...")
    image_paths: List[Path] = []
    for i, kw in enumerate(keywords):
        img = get_visual_for_segment(kw, i)
        image_paths.append(img)
        print(f"   [{i+1}/{len(keywords)}] Keyword '{kw}' -> {img.name}")
        
    # 6. FFmpeg Video Composition
    print("🎥 Step 4/4: Assembling video, Ken Burns effects, ducked audio, and sentence sync...")
    output_mp4 = OUTPUT_DIR / f"{script_id}.mp4"
    assemble_short_video(
        image_paths=image_paths,
        audio_path=audio_path,
        subtitle_ass_path=sub_path,
        output_mp4_path=output_mp4,
        total_duration=duration,
        bg_music_path=bg_music,
        segment_durations=segment_durations
    )
    
    # Save YouTube metadata companion file
    meta_path = OUTPUT_DIR / f"{script_id}_metadata.txt"
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"TITLE:\n{title or script_id}\n\n")
        f.write(f"DESCRIPTION:\n{description or ''}\n\n")
        f.write(f"SCRIPT:\n{text}\n")
        
    elapsed = time.time() - start_time
    print(f"\n✅ SUCCESS: Video rendered in {elapsed:.1f}s!")
    print(f"   Video:    {output_mp4}")
    print(f"   Metadata: {meta_path}\n")
    return output_mp4

def run_batch(json_file_path: Path):
    """Processes all scripts in a JSON file."""
    with open(json_file_path, "r", encoding="utf-8") as f:
        scripts = json.load(f)
        
    print(f"🚀 Starting batch generation of {len(scripts)} Shorts...")
    results = []
    for s in scripts:
        vid = process_short(
            script_id=s["id"],
            text=s["text"],
            keywords=s.get("keywords", ["nature", "universe", "mystery"]),
            title=s.get("title"),
            description=s.get("description"),
            voice=s.get("voice", DEFAULT_VOICE)
        )
        results.append(vid)
        
    print(f"\n🎉 All {len(results)} Shorts generated successfully in '{OUTPUT_DIR}'!")

def main():
    parser = argparse.ArgumentParser(description="100% Free Automated YouTube Shorts Generator")
    parser.add_argument("--batch", type=str, help="Path to batch JSON script file (e.g. scripts.json)")
    parser.add_argument("--id", type=str, help="Process specific script ID from scripts.json")
    parser.add_argument("--text", type=str, help="Direct script text to generate")
    parser.add_argument("--keywords", type=str, help="Comma-separated image keywords (e.g. 'space,galaxy,star')")
    parser.add_argument("--title", type=str, default="Daily Short #shorts", help="Video Title")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE, help="Edge-TTS Voice Name")
    
    args = parser.parse_args()
    
    if args.batch:
        run_batch(Path(args.batch))
    elif args.id:
        scripts_path = BASE_DIR / "scripts.json"
        with open(scripts_path, "r", encoding="utf-8") as f:
            scripts = json.load(f)
        target = next((s for s in scripts if s["id"] == args.id), None)
        if not target:
            print(f"Error: Script with ID '{args.id}' not found in {scripts_path}")
            sys.exit(1)
        process_short(
            script_id=target["id"],
            text=target["text"],
            keywords=target.get("keywords", ["mystery"]),
            title=target.get("title"),
            description=target.get("description"),
            voice=target.get("voice", DEFAULT_VOICE)
        )
    elif args.text:
        kws = [k.strip() for k in (args.keywords or "aesthetic,curiosity").split(",")]
        sid = f"custom_short_{int(time.time())}"
        process_short(
            script_id=sid,
            text=args.text,
            keywords=kws,
            title=args.title,
            voice=args.voice
        )
    else:
        # Default: process first script in scripts.json as a quick test
        scripts_path = BASE_DIR / "scripts.json"
        if scripts_path.exists():
            print("No arguments provided. Running default script from scripts.json as a test...")
            with open(scripts_path, "r", encoding="utf-8") as f:
                scripts = json.load(f)
            first = scripts[0]
            process_short(
                script_id=first["id"],
                text=first["text"],
                keywords=first.get("keywords", ["desert", "antarctica"]),
                title=first.get("title"),
                description=first.get("description"),
                voice=first.get("voice", DEFAULT_VOICE)
            )
        else:
            parser.print_help()

if __name__ == "__main__":
    main()
