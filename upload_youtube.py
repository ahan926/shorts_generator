"""Automated YouTube Uploader using the official YouTube Data API v3."""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE_DIR = Path(__file__).parent.resolve()
TOKEN_FILE = BASE_DIR / "token.json"
CLIENT_SECRETS_FILE = BASE_DIR / "client_secrets.json"

def get_authenticated_service():
    """Authenticates the user and returns the YouTube API client."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[Auth] Refreshing expired YouTube access token...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                print("\n❌ Missing 'client_secrets.json'!")
                print("----------------------------------------------------------------------")
                print("To upload automatically to your YouTube channel:")
                print("1. Go to https://console.cloud.google.com/apis/dashboard")
                print("2. Create a free project and enable 'YouTube Data API v3'")
                print("3. Go to 'Credentials' -> 'Create Credentials' -> 'OAuth client ID'")
                print("4. Choose Application type: 'Desktop app'")
                print("5. Download the JSON and save it as 'client_secrets.json' in this folder.")
                print("----------------------------------------------------------------------\n")
                sys.exit(1)
                
            print("[Auth] Opening browser for one-time YouTube authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
            print("[Auth] Authentication token saved to token.json.")

    return build("youtube", "v3", credentials=creds)

def parse_metadata_file(meta_path: Path) -> Dict[str, str]:
    """Parses companion _metadata.txt file."""
    meta = {"title": "Daily Short #shorts", "description": "", "script": ""}
    if not meta_path.exists():
        return meta
        
    content = meta_path.read_text(encoding="utf-8")
    parts = content.split("\n\n")
    for part in parts:
        if part.startswith("TITLE:\n"):
            meta["title"] = part.replace("TITLE:\n", "").strip()
        elif part.startswith("DESCRIPTION:\n"):
            meta["description"] = part.replace("DESCRIPTION:\n", "").strip()
        elif part.startswith("SCRIPT:\n"):
            meta["script"] = part.replace("SCRIPT:\n", "").strip()
    return meta

def upload_video(
    video_path: Path,
    title: Optional[str] = None,
    description: Optional[str] = None,
    privacy_status: str = "public",
    tags: Optional[list] = None
) -> str:
    """Uploads a video to YouTube and returns the video ID."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Check companion metadata
    companion_meta = video_path.with_name(f"{video_path.stem}_metadata.txt")
    if companion_meta.exists() and (not title or not description):
        parsed = parse_metadata_file(companion_meta)
        title = title or parsed.get("title")
        description = description or parsed.get("description")

    title = title or f"{video_path.stem} #shorts"
    description = description or "Automated daily short #shorts"
    tags = tags or ["shorts", "facts", "didyouknow", "curiosity"]

    print(f"\n🚀 Starting YouTube Upload...")
    print(f"   Video:   {video_path.name}")
    print(f"   Title:   {title}")
    print(f"   Privacy: {privacy_status}")

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],  # YouTube title limit
            "description": description[:5000],
            "tags": tags,
            "categoryId": "27"  # Education
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=1024 * 1024 * 2,  # 2MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   Uploading: {int(status.progress() * 100)}% complete...")

    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"\n🎉 UPLOAD COMPLETE!")
    print(f"   Video ID:  {video_id}")
    print(f"   Short URL: {video_url}\n")
    return video_id

def main():
    parser = argparse.ArgumentParser(description="Upload YouTube Shorts automatically via YouTube Data API v3")
    parser.add_argument("--video", type=str, required=True, help="Path to .mp4 video file to upload")
    parser.add_argument("--title", type=str, help="Custom video title (defaults to companion metadata)")
    parser.add_argument("--description", type=str, help="Custom description")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "private", "unlisted"], help="Visibility")
    
    args = parser.parse_args()
    upload_video(
        video_path=Path(args.video),
        title=args.title,
        description=args.description,
        privacy_status=args.privacy
    )

if __name__ == "__main__":
    main()
