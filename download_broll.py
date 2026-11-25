import os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("PEXELS_API_KEY")
headers = {"Authorization": api_key}
cache_dir = Path("cache")

queries = [
    ("insect on leaf close up", "broll_insect_leaf.mp4"),
    ("water splash slow motion", "broll_water_splash.mp4"),
    ("caterpillar on plant", "broll_caterpillar.mp4")
]

for q, filename in queries:
    target_path = cache_dir / filename
    if target_path.exists() and target_path.stat().st_size > 50000:
        print(f"Already have {filename}")
        continue
    url = "https://api.pexels.com/videos/search"
    resp = requests.get(url, headers=headers, params={"query": q, "per_page": 5}, timeout=10)
    if resp.status_code == 200:
        videos = resp.json().get("videos", [])
        if videos:
            v = videos[0]
            files = v.get("video_files", [])
            hd = [f for f in files if f.get("width") == 1080 or f.get("height") == 1080] or files
            download_url = hd[0]["link"]
            r = requests.get(download_url, stream=True, timeout=20)
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=64*1024):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded {filename} ({target_path.stat().st_size} bytes)")
