import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

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
    BASE_DIR
)
from tts_engine import generate_voiceover
from subtitles import generate_ass_subtitles
from stock_media import get_visual_for_segment
from compositor import assemble_short_video
from audio_ambient import generate_ambient_track

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
    voice: str = DEFAULT_VOICE
) -> Path:
    """End-to-end pipeline to generate a single Short."""
    print(f"\n==================================================")
    print(f"🎬 Generating Short: '{script_id}'")
    print(f"==================================================")
    
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
    
    # 4. Visual Media
    print(f"🖼️  Step 3/4: Fetching {len(keywords)} royalty-free visuals...")
    image_paths: List[Path] = []
    for i, kw in enumerate(keywords):
        img = get_visual_for_segment(kw, i)
        image_paths.append(img)
        print(f"   [{i+1}/{len(keywords)}] Keyword '{kw}' -> {img.name}")
        
    # 5. FFmpeg Video Composition
    print("🎥 Step 4/4: Assembling video, Ken Burns effects, and ducked audio...")
    output_mp4 = OUTPUT_DIR / f"{script_id}.mp4"
    assemble_short_video(
        image_paths=image_paths,
        audio_path=audio_path,
        subtitle_ass_path=sub_path,
        output_mp4_path=output_mp4,
        total_duration=duration,
        bg_music_path=bg_music
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
