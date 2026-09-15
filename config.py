"""Configuration settings for YouTube Shorts Generator."""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
MUSIC_DIR = ASSETS_DIR / "music"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"

# Ensure directories exist
for p in [IMAGES_DIR, MUSIC_DIR, OUTPUT_DIR, CACHE_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Video Specs (YouTube Shorts: 9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# Edge-TTS Settings (100% Free, Natural Azure Neural Voices)
# Options:
# "en-US-ChristopherNeural" (Deep, authoritative male, great for facts/curiosities)
# "en-US-GuyNeural" (Energetic, engaging male)
# "en-US-JennyNeural" (Warm, clear female)
# "en-US-AriaNeural" (Expressive female)
# "en-GB-RyanNeural" (British documentary narrator)
DEFAULT_VOICE = "en-US-ChristopherNeural"
VOICE_RATE = "+5%"  # slightly faster for snappy shorts retention
VOICE_PITCH = "+0Hz"

# Subtitle Styling (Modern Short viral style)
SUBTITLE_FONT = "Impact"  # Fallback to Arial Black / Arial if not installed
SUBTITLE_FONT_SIZE = 64
# Colors in ASS format: &HAABBGGRR& (AA=transparency, BB=blue, GG=green, RR=red)
SUBTITLE_PRIMARY_COLOR = "&H00FFFFFF&"   # White text
SUBTITLE_HIGHLIGHT_COLOR = "&H0000FFFF&" # Bright Yellow for active word (&H0000FFFF = Red:FF, Green:FF, Blue:00)
SUBTITLE_OUTLINE_COLOR = "&H00000000&"   # Deep black outline
SUBTITLE_OUTLINE_WIDTH = 4
SUBTITLE_SHADOW_DEPTH = 2

# Vertical placement (MarginV in pixels from bottom)
# For 1920 height, center safe zone is around 900-1100 to avoid UI overlays
SUBTITLE_MARGIN_V = 960

# Background Audio
MUSIC_VOLUME = 0.10  # 10% volume (ducked under voiceover)
