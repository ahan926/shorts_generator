import os
import json
import subprocess
import shutil
import wave
import numpy as np
from pathlib import Path
import imageio_ffmpeg
import edge_tts
import asyncio
from sfx_generator import generate_sub_impact, generate_whoosh

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
base_dir = Path(r"C:\Users\jpsh9\.gemini\antigravity\scratch\shorts_generator")
cache_dir = base_dir / "cache"
output_dir = base_dir / "output"
sfx_dir = cache_dir / "sfx"
temp_render_dir = cache_dir / "viral_render_segments"
temp_render_dir.mkdir(parents=True, exist_ok=True)

# 1. Voiceover (Guy Neural at +14% speed)
text = (
    "This fish is the deadliest sniper in the animal kingdom. "
    "It doesn't just spit water. "
    "The archerfish locks its grooved tongue against the roof of its mouth, shaping a biological rifle barrel. "
    "When it clamps its gill covers shut, the back of the water stream accelerates faster than the front, coalescing mid-air into a high-velocity water bullet. "
    "It hits with six times the impact needed to knock insects clean off overhanging branches. "
    "And that's why high-speed cameras revealed that..."
)

audio_path = cache_dir / "viral_archer_voice.mp3"

async def gen_voice():
    comm = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+14%", boundary="WordBoundary")
    words = []
    with open(audio_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "word": chunk["text"],
                    "start": chunk["offset"] / 10_000_000.0,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000.0
                })
    return words

words = asyncio.run(gen_voice())
total_duration = round(words[-1]["end"] + 0.15, 3)
print(f"Voiceover duration: {total_duration}s ({len(words)} words)")

# 2. Generate 2-word fast mobile ASS subtitles
def format_ass_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

ass_lines = [
    "[Script Info]",
    "Title: Viral High Retention Subtitles",
    "ScriptType: v4.00+",
    "PlayResX: 1080",
    "PlayResY: 1920",
    "WrapStyle: 0",
    "ScaledBorderAndShadow: yes",
    "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: Default,Impact,72,&H00FFFFFF&,&H0000FFFF&,&H00000000&,&H80000000,-1,0,0,0,100,100,1,0,1,5,3,5,0,0,0,1",
    "",
    "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
]

chunk_size = 2
for i in range(0, len(words), chunk_size):
    chunk = words[i:i+chunk_size]
    for w in chunk:
        st = format_ass_time(w["start"])
        et = format_ass_time(w["end"])
        phrase_parts = []
        for cw in chunk:
            clean = cw["word"].upper().strip()
            if cw == w:
                phrase_parts.append(f"{{\\c&H0000FFFF&}}{clean}{{\\c&H00FFFFFF&}}")
            else:
                phrase_parts.append(f"{clean}")
        phrase_text = " ".join(phrase_parts)
        ass_lines.append(f"Dialogue: 0,{st},{et},Default,,0,0,0,,{{\\pos(540,1120)}}{phrase_text}")

ass_path = temp_render_dir / "subtitles.ass"
with open(ass_path, "w", encoding="utf-8") as f:
    f.write("\n".join(ass_lines))
print("Generated rapid 2-word captions.")

# 3. Micro-cut visual segments (11 cuts across ~25.4s)
clips_sources = [
    (cache_dir / "vid_archerfish_pointed_snout_4.mp4", 0.0, 2.3),
    (cache_dir / "broll_caterpillar.mp4", 1.0, 2.1),
    (cache_dir / "vid_archerfish_swimming_forward_1.mp4", 1.0, 2.4),
    (cache_dir / "vid_archerfish_macro_stripes_2.mp4", 2.0, 2.3),
    (cache_dir / "broll_water_splash.mp4", 0.0, 2.3),
    (cache_dir / "broll_insect_leaf.mp4", 0.0, 2.4),
    (cache_dir / "broll_water_splash.mp4", 3.0, 2.4),
    (cache_dir / "vid_archerfish_cruising_surface_3.mp4", 1.0, 2.3),
    (cache_dir / "vid_archerfish_surface_school_0.mp4", 0.5, 2.3),
    (cache_dir / "vid_archerfish_macro_stripes_2.mp4", 5.0, 2.2),
    (cache_dir / "vid_archerfish_pointed_snout_4.mp4", 2.5, round(total_duration - 23.0, 3))
]

rendered_segment_clips = []
for idx, (src_path, start_t, dur) in enumerate(clips_sources):
    out_clip = temp_render_dir / f"seg_{idx:02d}.mp4"
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1,fps=30"
    )
    cmd = [
        ffmpeg_exe, "-y",
        "-ss", str(start_t),
        "-i", str(src_path),
        "-vf", vf,
        "-t", f"{dur:.3f}",
        "-an",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        str(out_clip)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rendered_segment_clips.append(out_clip)

concat_list = temp_render_dir / "concat_list.txt"
with open(concat_list, "w", encoding="utf-8") as f:
    for c in rendered_segment_clips:
        f.write(f"file '{c.resolve().as_posix()}'\n")

print(f"Rendered {len(rendered_segment_clips)} video micro-cuts.")

# 4. Generate composite SFX track in Python
sr = 44100
total_samples = int(sr * total_duration)
sfx_mix = np.zeros(total_samples, dtype=np.float32)

# Boom at t=0.0
boom_dur = 1.2
t_boom = np.linspace(0, boom_dur, int(sr * boom_dur), endpoint=False)
freq = 95.0 * np.exp(-3.5 * t_boom) + 32.0
phase = 2.0 * np.pi * np.cumsum(freq) / sr
sub = np.sin(phase) + 0.35 * np.sin(2.0 * phase)
env = np.where(t_boom < 0.008, t_boom / 0.008, np.exp(-3.2 * (t_boom - 0.008)))
boom_signal = np.tanh(sub * env * 1.5) * 0.90
end_boom = min(total_samples, len(boom_signal))
sfx_mix[:end_boom] += boom_signal[:end_boom]

# Whoosh function
whoosh_dur = 0.40
t_w = np.linspace(0, whoosh_dur, int(sr * whoosh_dur), endpoint=False)
noise = np.random.uniform(-1.0, 1.0, len(t_w))
w_env = (np.sin(np.pi * (t_w / whoosh_dur) ** 1.2) ** 2)
w_freq = 200.0 + 2200.0 * np.sin(np.pi * t_w / whoosh_dur)
w_carrier = np.sin(2.0 * np.pi * np.cumsum(w_freq) / sr)
whoosh_signal = (noise * 0.45 * w_env + w_carrier * 0.25 * w_env) * 0.65

# Cut timestamps:
cut_times = [2.3, 4.4, 6.8, 9.1, 11.4, 13.8, 16.2, 18.5, 20.8, 23.0]
for ct in cut_times:
    start_idx = int(ct * sr)
    end_idx = min(total_samples, start_idx + len(whoosh_signal))
    length = end_idx - start_idx
    if length > 0:
        sfx_mix[start_idx:end_idx] += whoosh_signal[:length]

sfx_mix = np.clip(sfx_mix, -1.0, 1.0)
sfx_pcm = (sfx_mix * 32767).astype(np.int16)
sfx_wav_path = temp_render_dir / "sfx_composite.wav"
with wave.open(str(sfx_wav_path), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    stereo = np.column_stack((sfx_pcm, sfx_pcm))
    wf.writeframes(stereo.tobytes())

print("Built composite sound design track (sub-boom + 10 transition whooshes).")

# 5. Final Assembly with FFmpeg
output_mp4 = output_dir / "viral_archerfish_sniper_upgrade.mp4"
bg_music = base_dir / "assets" / "music" / "ambient_pad.wav"

cmd = [
    ffmpeg_exe, "-y",
    "-f", "concat", "-safe", "0", "-i", "concat_list.txt",
    "-i", str(audio_path.resolve()),
    "-i", str(sfx_wav_path.resolve()),
    "-stream_loop", "-1", "-i", str(bg_music.resolve()),
    "-filter_complex",
    (
        "[0:v]subtitles=subtitles.ass[v];"
        "[1:a]volume=1.0[voice];"
        "[2:a]volume=0.85[sfx];"
        "[3:a]volume=0.10[bg];"
        "[voice][sfx][bg]amix=inputs=3:duration=first:dropout_transition=1[a]"
    ),
    "-map", "[v]",
    "-map", "[a]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-t", f"{total_duration:.3f}",
    str(output_mp4.resolve())
]

print("Rendering final upgraded short...")
subprocess.run(cmd, cwd=str(temp_render_dir), check=True)
print(f"🎉 SUCCESS! Upgraded short rendered to: {output_mp4}")
