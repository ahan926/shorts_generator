"""Royalty-free stock media provider supporting Pexels (Stock Videos & Photos),
Wikipedia/Wikimedia Commons (Free Public Domain), local folders, and fallback gradients.
"""
import os
import random
import requests
import re
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw
from config import (
    IMAGES_DIR,
    VIDEOS_DIR,
    CACHE_DIR,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    PEXELS_API_KEY,
    PREFER_STOCK_VIDEOS
)

HEADERS = {
    "User-Agent": "YouTubeShortsPipeline/1.0 (free automated pipeline; contact@domain.com)"
}

def generate_procedural_background(output_path: Path, theme: str = "curiosity") -> Path:
    """Generates a dark, high-contrast vertical gradient background as an instant fallback."""
    palette_options = [
        [(15, 12, 41), (48, 43, 99), (36, 36, 62)],      # Deep Cosmic Purple/Blue
        [(10, 24, 40), (20, 50, 80), (10, 15, 30)],      # Oceanic Abyss
        [(24, 18, 26), (56, 30, 48), (20, 10, 15)],      # Dark Crimson Mystery
        [(18, 22, 20), (30, 50, 40), (12, 20, 15)],      # Emerald Shadow
        [(20, 12, 8), (60, 30, 15), (25, 15, 10)],       # Warm Hardwood / Stadium Amber
    ]
    colors = random.choice(palette_options)
    
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), colors[0])
    draw = ImageDraw.Draw(img)
    
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
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95)
    return output_path

def fetch_pexels_video_scrape(keyword: str, output_path: Path) -> Optional[Path]:
    """Downloads portrait stock video from Pexels web search without requiring an API key."""
    try:
        url = f"https://www.pexels.com/search/videos/{keyword.replace(' ', '%20')}/?orientation=portrait"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
            
        mp4s = re.findall(r'https://videos\.pexels\.com/video-files/[^\s"\'<>]+\.mp4', resp.text)
        if not mp4s:
            return None
            
        best_mp4s = [u for u in mp4s if "1080_1920" in u or "720_1280" in u] or mp4s
        chosen_url = random.choice(best_mp4s)
        
        vid_resp = requests.get(chosen_url, headers=headers, stream=True, timeout=30)
        if vid_resp.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in vid_resp.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
            if output_path.stat().st_size > 50000:
                return output_path
    except Exception as e:
        pass
    return None

def fetch_pexels_video(keyword: str, output_path: Path) -> Optional[Path]:
    """
    Searches and downloads a royalty-free portrait stock video from Pexels.
    Uses official API if key provided, otherwise uses high-speed web video search.
    """
    api_key = PEXELS_API_KEY or os.getenv("PEXELS_API_KEY", "")
    if api_key:
        try:
            url = "https://api.pexels.com/videos/search"
            headers = {"Authorization": api_key, "User-Agent": "ShortsPipeline/1.0"}
            params = {
                "query": keyword,
                "orientation": "portrait",
                "per_page": 5
            }
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                videos = data.get("videos", [])
                if videos:
                    chosen_video = random.choice(videos)
                    video_files = chosen_video.get("video_files", [])
                    chosen_file = None
                    for vf in video_files:
                        if vf.get("file_type") == "video/mp4":
                            w = vf.get("width") or 0
                            h = vf.get("height") or 0
                            if h > w:
                                chosen_file = vf
                                break
                    if not chosen_file and video_files:
                        chosen_file = video_files[0]
                    if chosen_file and chosen_file.get("link"):
                        vid_resp = requests.get(chosen_file["link"], stream=True, timeout=30)
                        if vid_resp.status_code == 200:
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(output_path, "wb") as f:
                                for chunk in vid_resp.iter_content(chunk_size=1024 * 64):
                                    if chunk:
                                        f.write(chunk)
                            if output_path.stat().st_size > 50000:
                                return output_path
        except Exception as e:
            print(f"[Pexels API Video] Failed for '{keyword}': {e}")
            
    # Fallback to direct web video downloader
    return fetch_pexels_video_scrape(keyword, output_path)

def fetch_pexels_image_scrape(keyword: str, output_path: Path) -> Optional[Path]:
    """Downloads high-res portrait stock photo from Pexels web search."""
    try:
        url = f"https://www.pexels.com/search/{keyword.replace(' ', '%20')}/?orientation=portrait"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        imgs = re.findall(r'https://images\.pexels\.com/photos/[^\s"\'<>]+\.jpeg[^\s"\'<>]*', resp.text)
        if imgs:
            chosen = random.choice(imgs[:8])
            img_data = requests.get(chosen, headers=headers, timeout=15).content
            if len(img_data) > 10000:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_data)
                return output_path
    except Exception:
        pass
    return None

def fetch_pexels_image(keyword: str, output_path: Path) -> Optional[Path]:
    """Searches and downloads high-res portrait stock photo from Pexels."""
    api_key = PEXELS_API_KEY or os.getenv("PEXELS_API_KEY", "")
    if api_key:
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": api_key, "User-Agent": "ShortsPipeline/1.0"}
            params = {"query": keyword, "orientation": "portrait", "per_page": 5}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos:
                    chosen = random.choice(photos)
                    photo_url = chosen.get("src", {}).get("large2x") or chosen.get("src", {}).get("original")
                    if photo_url:
                        img_data = requests.get(photo_url, timeout=15).content
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(img_data)
                        return output_path
        except Exception as e:
            print(f"[Pexels API Photo] Failed for '{keyword}': {e}")
            
    return fetch_pexels_image_scrape(keyword, output_path)

def fetch_wikimedia_image(keyword: str, output_path: Path) -> Optional[Path]:
    """
    Searches and downloads a royalty-free / public-domain image from Wikipedia/Wikimedia.
    Tries primary keyword, then simplified fallback keywords if query has multiple words.
    """
    queries_to_try = [keyword]
    # If keyword is multiple words like "air jordan sneakers red", also try simpler subterms
    words = keyword.split()
    if len(words) > 2:
        queries_to_try.append(" ".join(words[:2]))
        queries_to_try.append(words[0])
        queries_to_try.append(words[1])

    for query in queries_to_try:
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": "6",
                "prop": "pageimages",
                "pithumbsize": "1280",
                "format": "json"
            }
            resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
            if resp.status_code != 200:
                continue
                
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                continue
                
            valid_urls = []
            for _, page in pages.items():
                thumb = page.get("thumbnail", {}).get("source")
                if thumb and not thumb.endswith(".svg"):
                    valid_urls.append(thumb)
                        
            if not valid_urls:
                continue
                
            chosen_url = random.choice(valid_urls)
            img_resp = requests.get(chosen_url, headers=HEADERS, timeout=12)
            if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_resp.content)
                return output_path
        except Exception as e:
            pass
            
    return None

def get_visual_for_segment(keyword: str, segment_index: int) -> Path:
    """
    Retrieves matching visual media (real stock video OR stock image) for a segment.
    Priority:
    1. Local user-placed video in assets/videos/{keyword}.mp4
    2. Local user-placed image in assets/images/{keyword}.jpg
    3. Pexels Stock Video (if PEXELS_API_KEY set and PREFER_STOCK_VIDEOS)
    4. Pexels Stock Photo (if PEXELS_API_KEY set)
    5. Wikipedia/Wikimedia Commons public domain photo
    6. High-contrast aesthetic procedural gradient (100% offline fallback)
    """
    clean_kw = keyword.replace(" ", "_")
    
    # 1. Local Video
    for ext in [".mp4", ".mov", ".webm"]:
        local_vid = VIDEOS_DIR / f"{keyword}{ext}"
        if local_vid.exists():
            return local_vid
            
    # 2. Local Image
    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
        local_img = IMAGES_DIR / f"{keyword}{ext}"
        if local_img.exists():
            return local_img

    # 3. Pexels Video
    if PREFER_STOCK_VIDEOS:
        cached_vid = CACHE_DIR / f"vid_{clean_kw}_{segment_index}.mp4"
        if cached_vid.exists():
            return cached_vid
        res_vid = fetch_pexels_video(keyword, cached_vid)
        if res_vid and res_vid.exists():
            return res_vid

    # 4. Pexels Photo
    cached_img = CACHE_DIR / f"img_{clean_kw}_{segment_index}.jpg"
    if cached_img.exists():
        return cached_img
    res_img = fetch_pexels_image(keyword, cached_img)
    if res_img and res_img.exists():
        return res_img

    # 5. Wikimedia Commons
    res_wiki = fetch_wikimedia_image(keyword, cached_img)
    if res_wiki and res_wiki.exists():
        return res_wiki

    # 6. Fallback gradient
    fallback_path = CACHE_DIR / f"bg_fallback_{clean_kw}_{segment_index}.jpg"
    return generate_procedural_background(fallback_path)
