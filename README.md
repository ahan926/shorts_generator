# 🚀 100% Free Automated YouTube Shorts Generator

A fully automated, zero-cost pipeline designed to generate high-retention, royalty-free YouTube Shorts ready for daily uploading.

---

## 💡 Why This is 100% Free (Zero Subscriptions)

Unlike expensive SaaS tools ($30–$50/mo), this entire pipeline runs locally on your machine with zero fees:
1. **Voiceovers:** Powered by **Microsoft Azure Neural TTS** (via `edge-tts`) — realistic, human-like narration without any API keys or subscriptions.
2. **Visuals:** Automatically retrieves public-domain and Creative Commons stock imagery from **Wikimedia Commons** and **Pexels** (with procedural gradient fallbacks if offline).
3. **Subtitles:** Frame-accurate animated **karaoke-style ASS subtitles** highlighting words as they are spoken.
4. **Video Engine:** High-performance **FFmpeg** rendering with smooth Ken Burns cinematic zooms and audio ducking.

---

## 🛠️ Quick Start

### 1. Run with `uv` (Recommended — zero manual setup)
`uv` automatically installs dependencies and runs the script in an isolated sandbox:

```powershell
cd C:\Users\jpsh9\.gemini\antigravity\scratch\shorts_generator

# Generate the first test Short:
& "C:\Users\jpsh9\.local\bin\uv.exe" run python generate.py

# Batch generate all 5 preloaded viral Shorts:
& "C:\Users\jpsh9\.local\bin\uv.exe" run python generate.py --batch scripts.json
```

### 2. Generate a Custom One-Off Short
```powershell
& "C:\Users\jpsh9\.local\bin\uv.exe" run python generate.py `
  --text "Did you know that honey never spoils? Archaeologists have found pots of honey in ancient Egyptian tombs that are over three thousand years old and still perfectly edible." `
  --keywords "ancient egypt pyramids, golden honey jar, archeology tomb" `
  --title "The Only Food That Never Spoils 🍯 #shorts #facts"
```

---

## 📁 Project Structure

```
shorts_generator/
│
├── generate.py           # Main CLI runner (single or batch)
├── config.py             # Colors, font sizes, resolution (1080x1920), voices
├── tts_engine.py         # Free neural voice synthesis + word timestamps
├── subtitles.py          # Dynamic karaoke ASS subtitle generator
├── compositor.py         # FFmpeg video editor (zoom, audio ducking, sub burn)
├── stock_media.py        # Royalty-free Wikimedia/Pexels image search
├── audio_ambient.py      # Procedural ambient background pad generator
├── scripts.json          # Batch list of scripts to produce
│
├── assets/
│   ├── images/           # Drop your own custom JPG/PNG files here (optional)
│   └── music/            # Drop free royalty-free MP3/WAV tracks here (optional)
│
└── output/               # Generated MP4 videos + YouTube metadata (.txt)
```

---

## 🤖 The "30-Day Batch" Script Prompt (For ChatGPT or Gemini)

Copy and paste this prompt into free ChatGPT or Gemini to generate 15 to 30 scripts formatted directly for `scripts.json`:

```text
Act as a YouTube Shorts viral retention expert. Write 5 high-hook scripts (30 to 45 seconds each, 70-85 words) about mind-blowing paradoxes or bizarre facts.

Rules:
1. Hook (0-3s): State a counter-intuitive claim or question immediately.
2. Body (3-25s): Deliver 2-3 fast facts with zero filler words.
3. Loop (last 3s): Make the final sentence connect seamlessly back to the opening line.
4. Output in valid JSON format matching this schema:
[
  {
    "id": "short_slug_name",
    "title": "Clickable YouTube Title with 1-2 Emojis and #shorts",
    "description": "2-line YouTube description with tags",
    "text": "The exact spoken script here.",
    "keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4"]
  }
]
```

---

## 📅 The Daily Upload Strategy (15 Minutes Once a Week)

1. **Sunday Evening:** Run the batch generator to create 7 videos into the `output/` folder.
2. **Open YouTube Studio:** (studio.youtube.com)
3. **Bulk Upload:** Drag all 7 `.mp4` files into the upload window.
4. **Copy Metadata:** Open the companion `_metadata.txt` file generated for each video, paste the title and description.
5. **Schedule:**
   - Video 1 -> Monday at 1:00 PM (or your peak time)
   - Video 2 -> Tuesday at 1:00 PM
   - Video 3 -> Wednesday at 1:00 PM
   - ...and so on.
6. Done! Your channel runs on autopilot for the entire week.
