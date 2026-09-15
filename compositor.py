"""Video composition pipeline using FFmpeg to combine audio, stock imagery, 
Ken Burns animations, and animated ASS subtitles.
"""
import math
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
import imageio_ffmpeg

from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    MUSIC_VOLUME,
    CACHE_DIR,
    MUSIC_DIR
)

def get_ffmpeg_binary() -> str:
    """Gets the path to the ffmpeg executable provided by imageio-ffmpeg."""
    return imageio_ffmpeg.get_ffmpeg_exe()

def create_segment_clip(
    media_path: Path,
    duration: float,
    output_clip_path: Path,
    zoom_in: bool = True
) -> Path:
    """
    Creates an animated 1080x1920 30fps MP4 segment from either:
    - A stock video clip (center-cropped, looped if needed, trimmed to duration)
    - A static stock image (Ken Burns zoompan animation)
    """
    ffmpeg_exe = get_ffmpeg_binary()
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    
    is_video = media_path.suffix.lower() in [".mp4", ".mov", ".webm", ".mkv"]
    
    if is_video:
        vf_filter = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},fps={VIDEO_FPS}"
        )
        cmd = [
            ffmpeg_exe,
            "-y",
            "-stream_loop", "-1",
            "-i", str(media_path.resolve()),
            "-vf", vf_filter,
            "-t", f"{duration:.3f}",
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            str(output_clip_path.resolve())
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            return output_clip_path
        # If video processing failed, fallback to treating as static frame
    
    total_frames = max(1, int(duration * VIDEO_FPS))
    
    # Zoom expression: slow zoom in or zoom out
    if zoom_in:
        zoom_expr = "min(pzoom+0.0015,1.25)"
    else:
        zoom_expr = "if(eq(on,1),1.25,max(1.0,pzoom-0.0015))"
        
    vf_filter = (
        f"scale=-1:2160,crop=1215:2160,"
        f"zoompan=z='{zoom_expr}':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}"
    )
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-loop", "1",
        "-i", str(media_path.resolve()),
        "-vf", vf_filter,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        str(output_clip_path.resolve())
    ]
    
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        fallback_vf = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},fps={VIDEO_FPS}"
        cmd_fallback = [
            ffmpeg_exe, "-y", "-loop", "1", "-i", str(media_path.resolve()),
            "-vf", fallback_vf, "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            str(output_clip_path.resolve())
        ]
        subprocess.run(cmd_fallback, check=True)
        
    return output_clip_path

def assemble_short_video(
    image_paths: List[Path],
    audio_path: Path,
    subtitle_ass_path: Path,
    output_mp4_path: Path,
    total_duration: float,
    bg_music_path: Optional[Path] = None
) -> Path:
    """
    Renders the final YouTube Short:
    1. Cuts/animates images across total duration.
    2. Concatenates video segments.
    3. Burns ASS subtitles in the safe zone.
    4. Mixes voiceover audio with ducked background music.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = CACHE_DIR / f"render_{output_mp4_path.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    num_images = len(image_paths)
    if num_images == 0:
        raise ValueError("No images provided for video generation.")

    # Calculate duration per image (e.g. 4-6 seconds per image)
    dur_per_img = total_duration / num_images
    segment_clips: List[Path] = []
    
    for i, img in enumerate(image_paths):
        clip_path = temp_dir / f"clip_{i:02d}.mp4"
        zoom_direction = (i % 2 == 0)
        create_segment_clip(img, dur_per_img, clip_path, zoom_in=zoom_direction)
        segment_clips.append(clip_path)

    # Create concat list
    concat_list_file = temp_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in segment_clips:
            # Escape path for ffmpeg concat demuxer
            clean_p = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    # Prepare subtitle file in temp_dir
    local_sub_path = temp_dir / "subtitles.ass"
    shutil.copy(subtitle_ass_path, local_sub_path)
    
    # Subtitle filter using relative path inside temp_dir
    video_filter = "subtitles=subtitles.ass"

    # Check for background music in assets/music/
    if bg_music_path is None or not bg_music_path.exists():
        available_music = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
        if available_music:
            bg_music_path = available_music[0]

    # Build final FFmpeg command
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "concat_list.txt",
        "-i", str(audio_path.resolve()),
    ]

    if bg_music_path and bg_music_path.exists():
        cmd.extend([
            "-stream_loop", "-1",
            "-i", str(bg_music_path.resolve()),
            "-filter_complex",
            (
                f"[0:v]{video_filter}[v];"
                f"[2:a]volume={MUSIC_VOLUME}[bg];"
                f"[1:a]volume=1.0[voice];"
                f"[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[a]"
            ),
            "-map", "[v]",
            "-map", "[a]",
        ])
    else:
        cmd.extend([
            "-vf", video_filter,
            "-map", "0:v",
            "-map", "1:a",
        ])

    cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "19",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_duration:.3f}",
        str(output_mp4_path.resolve())
    ])

    result = subprocess.run(
        cmd,
        cwd=str(temp_dir.resolve()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg render error: {result.stderr}")

    return output_mp4_path
