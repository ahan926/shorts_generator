"""Royalty-free stock media provider and dynamic visual processor.
Supports Wikimedia Commons (No API key needed), Pexels (optional free key),
local asset folders, and procedural high-contrast backgrounds.
"""
import os
import random
import requests
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw
from config import IMAGES_DIR, CACHE_DIR, VIDEO_WIDTH, VIDEO_HEIGHT

HEADERS = {
    "User-Agent": "YouTubeShortsGenerator/1.0 (free automated pipeline; contact@example.com)"
}

def generate_procedural_background(output_path: Path, theme: str = "curiosity") -> Path:
    """
    Generates a dark, high-contrast vertical gradient background as an instant fallback.
    Ensures the generator works 100% offline with zero dependencies on external APIs.
    """
    palette_options = [
        [(15, 12, 41), (48, 43, 99), (36, 36, 62)],      # Deep Cosmic Purple/Blue
        [(10, 24, 40), (20, 50, 80), (10, 15, 30)],      # Oceanic Abyss
        [(24, 18, 26), (56, 30, 48), (20, 10, 15)],      # Dark Crimson Mystery
        [(18, 22, 20), (30, 50, 40), (12, 20, 15)],      # Emerald Shadow
    ]
    colors = random.choice(palette_options)
    
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), colors[0])
    draw = ImageDraw.Draw(img)
    
    # Draw smooth vertical multi-stop gradient
    steps = VIDEO_HEIGHT
    for y in range(steps):
        t = y / steps
        if t < 0.5:
            local_t = t * 2
            c1, c2 = colors[0], colors[1]
        else:
            local_t = (t - 0.5) * 2
            c1, c2 = colors[1], colors[2]
            
        r = int(c1[0] + (c2[0] - c1[0]) * local_t)
        g = int(c1[1] + (c2[1] - c1[1]) * local_t)
        b = int(c1[2] + (c2[2] - c1[2]) * local_t)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))
        
    # Add subtle vignette overlay
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95)
    return output_path

def fetch_wikimedia_image(keyword: str, output_path: Path) -> Optional[Path]:
    """
    Searches and downloads a royalty-free / public-domain image from Wikipedia/Wikimedia.
    Requires NO API keys and is 100% free and open.
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": keyword,
            "gsrlimit": "6",
            "prop": "pageimages",
            "pithumbsize": "1280",
            "format": "json"
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
            
        valid_urls = []
        for _, page in pages.items():
            thumb = page.get("thumbnail", {}).get("source")
            if thumb and not thumb.endswith(".svg"):
                valid_urls.append(thumb)
                    
        if not valid_urls:
            return None
            
        chosen_url = random.choice(valid_urls)
        img_resp = requests.get(chosen_url, headers=HEADERS, timeout=12)
        if img_resp.status_code == 200 and len(img_resp.content) > 5000:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_resp.content)
            return output_path
    except Exception as e:
        print(f"[StockMedia] Wikimedia search failed for '{keyword}': {e}")
        
    return None

def fetch_pexels_image(keyword: str, output_path: Path) -> Optional[Path]:
    """Fetches high-res portrait image from Pexels if PEXELS_API_KEY is available."""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return None
        
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}
        params = {"query": keyword, "orientation": "portrait", "per_page": 5}
        resp = requests.get(url, headers=headers, params=params, timeout=8)
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            if photos:
                photo_url = random.choice(photos)["src"]["large2x"]
                img_data = requests.get(photo_url, timeout=12).content
                with open(output_path, "wb") as f:
                    f.write(img_data)
                return output_path
    except Exception as e:
        print(f"[StockMedia] Pexels search failed for '{keyword}': {e}")
        
    return None

def get_visual_for_segment(keyword: str, segment_index: int) -> Path:
    """
    Returns an image path for a video segment.
    Priority:
    1. Local user-placed image matching keyword in assets/images/
    2. Pexels (if API key set)
    3. Wikimedia Commons (Free Public Domain)
    4. Procedural aesthetic background (100% offline reliable fallback)
    """
    # 1. Check local assets
    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
        candidate = IMAGES_DIR / f"{keyword}{ext}"
        if candidate.exists():
            return candidate
            
    cached_img = CACHE_DIR / f"img_{keyword}_{segment_index}.jpg"
    if cached_img.exists():
        return cached_img

    # 2. Try Pexels
    result = fetch_pexels_image(keyword, cached_img)
    if result and result.exists():
        return result

    # 3. Try Wikimedia Commons
    result = fetch_wikimedia_image(keyword, cached_img)
    if result and result.exists():
        return result

    # 4. Fallback to procedural background
    fallback_path = CACHE_DIR / f"bg_fallback_{segment_index}.jpg"
    return generate_procedural_background(fallback_path)
