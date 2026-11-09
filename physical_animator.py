"""
Complete Physical 3D Mechanism Animator
Renders cinematic, photorealistic 1080x1920 30fps physical anatomical animations
based on 3D biological renders — ZERO graphs, ZERO HUD boxes, ZERO text.
"""
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple
import cv2
import numpy as np

from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ASSETS_IMAGES = Path("assets/images")
ASSETS_VIDEOS = Path("assets/videos")
ASSETS_VIDEOS.mkdir(parents=True, exist_ok=True)

def get_ffmpeg_binary() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def load_and_fit_base_image(image_path: Path) -> np.ndarray:
    """Loads a 3D physical render and center-crops/scales it to 1080x1920 BGR numpy array."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")
    h, w = img.shape[:2]
    scale = max(VIDEO_WIDTH / w, VIDEO_HEIGHT / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    x1 = (new_w - VIDEO_WIDTH) // 2
    y1 = (new_h - VIDEO_HEIGHT) // 2
    cropped = resized[y1:y1 + VIDEO_HEIGHT, x1:x1 + VIDEO_WIDTH]
    return cropped

def save_and_transcode_frames(frames: List[np.ndarray], output_path: Path):
    temp_raw = output_path.with_suffix(".temp.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(str(temp_raw), fourcc, VIDEO_FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))
    for f in frames:
        out_video.write(f)
    out_video.release()

    ffmpeg_exe = get_ffmpeg_binary()
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(temp_raw.resolve()),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        str(output_path.resolve())
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    temp_raw.unlink(missing_ok=True)

# -------------------------------------------------------------
# 1. SPIDER PHYSICAL ANIMATIONS
# -------------------------------------------------------------
def animate_spider_hydraulic_pump(output_path: Path, duration: float = 6.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "spider_hydraulic_physical_anatomy.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    num_particles = 70
    np.random.seed(42)
    p_offsets = np.random.uniform(0, 1, num_particles)
    p_radii = np.random.uniform(3, 8, num_particles)
    p_speeds = np.random.uniform(0.6, 1.4, num_particles)

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        zoom = 1.0 + progress * 0.08
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5), int(h * 0.48)
        x1 = max(0, cx - cur_w // 2)
        y1 = max(0, cy - cur_h // 2)
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        overlay = np.zeros_like(frame)
        pulse = (math.sin(t * 4.0) + 1.0) / 2.0
        surge_intensity = 0.4 + pulse * 0.6

        chamber_center = (int(VIDEO_WIDTH * 0.5), int(VIDEO_HEIGHT * 0.42))
        chamber_r = int(70 + pulse * 25)
        cv2.circle(overlay, chamber_center, chamber_r, (255, 230, 0), -1)

        conduits = [
            [(int(VIDEO_WIDTH * 0.46), int(VIDEO_HEIGHT * 0.45)),
             (int(VIDEO_WIDTH * 0.32), int(VIDEO_HEIGHT * 0.55)),
             (int(VIDEO_WIDTH * 0.22), int(VIDEO_HEIGHT * 0.72)),
             (int(VIDEO_WIDTH * 0.16), int(VIDEO_HEIGHT * 0.88))],
            [(int(VIDEO_WIDTH * 0.54), int(VIDEO_HEIGHT * 0.45)),
             (int(VIDEO_WIDTH * 0.68), int(VIDEO_HEIGHT * 0.55)),
             (int(VIDEO_WIDTH * 0.78), int(VIDEO_HEIGHT * 0.72)),
             (int(VIDEO_WIDTH * 0.84), int(VIDEO_HEIGHT * 0.88))]
        ]

        for path in conduits:
            pts = np.array(path, np.int32).reshape((-1, 1, 2))
            cv2.polylines(overlay, [pts], isClosed=False, color=(255, 200, 40), thickness=int(18 + pulse * 12))
            for p_idx in range(num_particles // 2):
                pos = (p_offsets[p_idx] + t * p_speeds[p_idx] * 0.8) % 1.0
                segment = pos * (len(path) - 1)
                s_idx = int(segment)
                frac = segment - s_idx
                if s_idx < len(path) - 1:
                    px = int(path[s_idx][0] + frac * (path[s_idx + 1][0] - path[s_idx][0]))
                    py = int(path[s_idx][1] + frac * (path[s_idx + 1][1] - path[s_idx][1]))
                    cv2.circle(overlay, (px, py), int(p_radii[p_idx]), (255, 255, 180), -1)

        glow = cv2.GaussianBlur(overlay, (51, 51), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, float(0.65 * surge_intensity), 0)

        if (t % 1.5) < 0.2:
            snap_frac = (t % 1.5) / 0.2
            shock_r = int(snap_frac * 300)
            cv2.circle(blended, chamber_center, shock_r, (255, 255, 255), max(1, int(6 * (1.0 - snap_frac))))

        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def animate_spider_hydraulic_launch(output_path: Path, duration: float = 7.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "spider_hydraulic_leg_piston.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        pan_y = int(math.sin(progress * math.pi) * 60)
        zoom = 1.0 + (math.sin(t * 1.2) + 1.0) * 0.04
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5), int(h * 0.5 + pan_y)
        x1 = max(0, min(w - cur_w, cx - cur_w // 2))
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        overlay = np.zeros_like(frame)
        joint_cx, joint_cy = int(VIDEO_WIDTH * 0.52), int(VIDEO_HEIGHT * 0.48)
        fluid_level = (math.sin(t * 3.5) + 1.0) / 2.0
        cv2.ellipse(overlay, (joint_cx, joint_cy), (int(90 + fluid_level * 40), int(140 + fluid_level * 50)),
                    35, 0, 360, (255, 220, 50), -1)

        for stream_i in range(8):
            s_offset = (t * 2.5 + stream_i * 0.3) % 1.0
            sx = int(VIDEO_WIDTH * 0.3 + s_offset * (joint_cx - VIDEO_WIDTH * 0.3))
            sy = int(VIDEO_HEIGHT * 0.7 + s_offset * (joint_cy - VIDEO_HEIGHT * 0.7))
            cv2.circle(overlay, (sx, sy), int(6 + math.sin(s_offset * math.pi) * 8), (255, 255, 200), -1)

        glow = cv2.GaussianBlur(overlay, (45, 45), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, float(0.7 * (0.5 + fluid_level * 0.5)), 0)

        if fluid_level > 0.92:
            flash_intensity = (fluid_level - 0.92) / 0.08
            flash = np.full_like(blended, (int(40 * flash_intensity), int(180 * flash_intensity), int(220 * flash_intensity)))
            blended = cv2.add(blended, flash)

        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

# -------------------------------------------------------------
# 2. CHAMELEON PHYSICAL ANIMATIONS
# -------------------------------------------------------------
def animate_chameleon_iridophores(output_path: Path, duration: float = 6.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "chameleon_iridophore_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        # Slow cinematic downward scan through the physical skin layers
        pan_y = int(progress * 120)
        zoom = 1.02 + math.sin(progress * math.pi) * 0.04
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        x1 = (w - cur_w) // 2
        y1 = max(0, min(h - cur_h, pan_y))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Prismatic sparkling glints across the physical guanine nanocrystals
        overlay = np.zeros_like(frame)
        sparkle_phase = t * 3.0
        np.random.seed(99)
        for _ in range(25):
            sx = int(np.random.uniform(VIDEO_WIDTH * 0.2, VIDEO_WIDTH * 0.8))
            sy = int(np.random.uniform(VIDEO_HEIGHT * 0.45, VIDEO_HEIGHT * 0.75))
            flicker = (math.sin(sparkle_phase + np.random.uniform(0, 10)) + 1.0) / 2.0
            if flicker > 0.6:
                cv2.circle(overlay, (sx, sy), int(4 + flicker * 6), (255, 255, 200), -1)
                cv2.line(overlay, (sx - 12, sy), (sx + 12, sy), (255, 255, 255), 1)
                cv2.line(overlay, (sx, sy - 12), (sx, sy + 12), (255, 255, 255), 1)

        glow = cv2.GaussianBlur(overlay, (21, 21), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.75, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def animate_chameleon_lattice_shift(output_path: Path, duration: float = 7.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "chameleon_iridophore_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = (math.sin(t * 1.4 - math.pi / 2) + 1.0) / 2.0 # 0.0 (green) to 1.0 (crimson red)
        zoom = 1.05 + progress * 0.06
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        x1 = (w - cur_w) // 2
        y1 = (h - cur_h) // 2
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Organic hue transformation in the nanocrystal layer: green -> amber -> red
        # In BGR: boost Red channel, reduce Green/Blue in crystal zone
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        # Shift hue (Green is ~60 in OpenCV, Red is ~0/180)
        mask = (hsv[:, :, 1] > 30).astype(np.float32) # saturated areas
        # Shift hue toward red as progress increases
        hsv[:, :, 0] = (hsv[:, :, 0] - progress * 45) % 180
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 + progress * 0.35), 0, 255) # increase saturation
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1.0 + progress * 0.2), 0, 255)
        shifted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Blend smooth transition
        blended = cv2.addWeighted(frame, 1.0 - progress, shifted, progress, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

# -------------------------------------------------------------
# 3. HUMMINGBIRD PHYSICAL ANIMATIONS
# -------------------------------------------------------------
def animate_hummingbird_figure_eight(output_path: Path, duration: float = 6.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "hummingbird_vortex_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        # High speed camera drift with subtle vibration matching 80Hz flap
        vibe_x = int(math.sin(t * 80.0) * 3)
        vibe_y = int(math.cos(t * 80.0) * 2)
        zoom = 1.0 + math.sin(progress * math.pi) * 0.05
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5 + vibe_x), int(h * 0.45 + vibe_y)
        x1 = max(0, min(w - cur_w, cx - cur_w // 2))
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Dynamic physical airflow vapor pulses flowing behind wings
        overlay = np.zeros_like(frame)
        for trail_i in range(12):
            tr_t = (t * 2.0 + trail_i * 0.15) % 1.0
            tx = int(VIDEO_WIDTH * 0.5 + math.sin(tr_t * math.pi * 2) * 280)
            ty = int(VIDEO_HEIGHT * 0.4 + math.sin(tr_t * math.pi * 4) * 110)
            tr_r = int(12 + tr_t * 28)
            cv2.circle(overlay, (tx, ty), tr_r, (255, 240, 200), -1)

        glow = cv2.GaussianBlur(overlay, (41, 41), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.4, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def animate_hummingbird_vortex_lift(output_path: Path, duration: float = 7.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "hummingbird_vortex_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        zoom = 1.04 + progress * 0.08
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5), int(h * 0.42)
        x1 = (w - cur_w) // 2
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Swirling Leading-Edge Vortex (LEV) mini-tornado rings over the physical wing
        overlay = np.zeros_like(frame)
        vx, vy = int(VIDEO_WIDTH * 0.48), int(VIDEO_HEIGHT * 0.38)
        for ring_i in range(6):
            r = int(30 + ring_i * 22)
            rot = (t * 400 + ring_i * 60) % 360
            cv2.ellipse(overlay, (vx, vy), (r, int(r * 0.45)), int(rot), 0, 260, (255, 230, 140), 4)

        glow = cv2.GaussianBlur(overlay, (31, 31), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.55, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

# -------------------------------------------------------------
# 4. WOODPECKER PHYSICAL ANIMATIONS
# -------------------------------------------------------------
def animate_woodpecker_cranial_shock(output_path: Path, duration: float = 6.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "woodpecker_hyoid_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        zoom = 1.0 + progress * 0.06
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.52), int(h * 0.46)
        x1 = max(0, min(w - cur_w, cx - cur_w // 2))
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Kinetic strike shockwave ripples through beak into spongy forehead bone
        overlay = np.zeros_like(frame)
        strike_time = (t * 3.0) % 1.0
        if strike_time < 0.35:
            shock_frac = strike_time / 0.35
            bx, by = int(VIDEO_WIDTH * 0.68), int(VIDEO_HEIGHT * 0.48) # beak/frontal skull
            for sw_i in range(3):
                sr = int((shock_frac * 220) - sw_i * 40)
                if sr > 0:
                    cv2.circle(overlay, (bx, by), sr, (80, 160, 255), max(1, int(5 * (1.0 - shock_frac))))

        glow = cv2.GaussianBlur(overlay, (25, 25), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.7, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def animate_woodpecker_hyoid_seatbelt(output_path: Path, duration: float = 7.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "woodpecker_hyoid_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        # Slow pan tracing the 360-degree looping hyoid sling around the skull
        pan_y = int(math.sin(progress * math.pi) * 80)
        zoom = 1.03 + math.sin(t * 1.5) * 0.03
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5), int(h * 0.48 + pan_y)
        x1 = max(0, min(w - cur_w, cx - cur_w // 2))
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Pulsing tension glow along the physical hyoid bone harness wrapping the cranium
        overlay = np.zeros_like(frame)
        tension = (math.sin(t * 5.0) + 1.0) / 2.0
        # Highlight loop around skull
        sk_cx, sk_cy = int(VIDEO_WIDTH * 0.48), int(VIDEO_HEIGHT * 0.46)
        cv2.ellipse(overlay, (sk_cx, sk_cy), (int(180 + tension * 15), int(220 + tension * 20)),
                    -15, 0, 360, (60, 220, 255), int(8 + tension * 6))

        glow = cv2.GaussianBlur(overlay, (35, 35), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, float(0.65 * tension), 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

# -------------------------------------------------------------
# 5. OWL PHYSICAL ANIMATIONS
# -------------------------------------------------------------
def animate_owl_comb_serrations(output_path: Path, duration: float = 6.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "owl_comb_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        zoom = 1.02 + progress * 0.08
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.48), int(h * 0.5)
        x1 = max(0, min(w - cur_w, cx - cur_w // 2))
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Smooth physical laminar air smoke streams parting across the comb teeth
        overlay = np.zeros_like(frame)
        for line_i in range(10):
            ly = int(VIDEO_HEIGHT * 0.25 + line_i * 60)
            offset = (t * 200 + line_i * 40) % VIDEO_WIDTH
            cv2.line(overlay, (int(offset), ly), (int(offset + 180), ly), (220, 240, 255), 3)

        glow = cv2.GaussianBlur(overlay, (25, 25), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.45, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def animate_owl_trailing_fringe(output_path: Path, duration: float = 7.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "owl_comb_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        pan_x = int(math.sin(progress * math.pi) * 60)
        zoom = 1.05 + math.sin(t * 1.5) * 0.03
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5 + pan_x), int(h * 0.52)
        x1 = max(0, min(w - cur_w, cx - cur_w // 2))
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Soft specular sheen moving across velvety down
        overlay = np.zeros_like(frame)
        sheen_x = int((t * 180) % (VIDEO_WIDTH + 300) - 150)
        cv2.line(overlay, (sheen_x, 0), (sheen_x + 200, VIDEO_HEIGHT), (255, 240, 210), 40)
        glow = cv2.GaussianBlur(overlay, (81, 81), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.35, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

# -------------------------------------------------------------
# 6. JELLYFISH PHYSICAL ANIMATIONS
# -------------------------------------------------------------
def animate_jellyfish_cnidocyte(output_path: Path, duration: float = 6.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "jellyfish_harpoon_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        # Gentle deep-sea fluid floating drift
        drift_x = int(math.sin(t * 1.2) * 15)
        drift_y = int(math.cos(t * 1.0) * 20)
        zoom = 1.0 + progress * 0.06
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5 + drift_x), int(h * 0.5 + drift_y)
        x1 = max(0, min(w - cur_w, cx - cur_w // 2))
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Bioluminescent osmotic pressure pulsation inside the capsule
        overlay = np.zeros_like(frame)
        pulse = (math.sin(t * 3.0) + 1.0) / 2.0
        cap_cx, cap_cy = int(VIDEO_WIDTH * 0.48), int(VIDEO_HEIGHT * 0.55)
        cv2.circle(overlay, (cap_cx, cap_cy), int(110 + pulse * 45), (255, 180, 50), -1)

        glow = cv2.GaussianBlur(overlay, (61, 61), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, float(0.65 * pulse), 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def animate_jellyfish_harpoon_launch(output_path: Path, duration: float = 7.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "jellyfish_harpoon_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        zoom = 1.04 + progress * 0.08
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5), int(h * 0.45)
        x1 = (w - cur_w) // 2
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Explosive venom droplet dispersion and acoustic shockwave in ocean water
        overlay = np.zeros_like(frame)
        tip_x, tip_y = int(VIDEO_WIDTH * 0.5), int(VIDEO_HEIGHT * 0.35)
        shock_cycle = (t * 2.5) % 1.0
        # Expanding shockwave rings
        sr = int(shock_cycle * 260)
        cv2.circle(overlay, (tip_x, tip_y), sr, (255, 255, 180), max(1, int(6 * (1.0 - shock_cycle))))

        # Venom droplets spraying outward
        np.random.seed(77)
        for d_i in range(18):
            ang = np.random.uniform(0, 2 * math.pi)
            dist = shock_cycle * np.random.uniform(80, 240)
            dx = int(tip_x + math.cos(ang) * dist)
            dy = int(tip_y + math.sin(ang) * dist)
            cv2.circle(overlay, (dx, dy), int(3 + np.random.uniform(1, 4)), (0, 255, 220), -1)

        glow = cv2.GaussianBlur(overlay, (21, 21), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.7, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

# -------------------------------------------------------------
# 7. BUTTERFLY CHRYSALIS PHYSICAL ANIMATIONS
# -------------------------------------------------------------
def animate_butterfly_autolysis(output_path: Path, duration: float = 6.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "butterfly_chrysalis_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        zoom = 1.0 + progress * 0.05
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5), int(h * 0.5)
        x1 = (w - cur_w) // 2
        y1 = (h - cur_h) // 2
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Swirling golden nutrient broth convection particles
        overlay = np.zeros_like(frame)
        pod_cx, pod_cy = int(VIDEO_WIDTH * 0.5), int(VIDEO_HEIGHT * 0.55)
        np.random.seed(33)
        for p_i in range(25):
            radius = np.random.uniform(40, 160)
            speed = np.random.uniform(0.8, 2.0)
            angle = t * speed + np.random.uniform(0, 2 * math.pi)
            px = int(pod_cx + math.cos(angle) * radius)
            py = int(pod_cy + math.sin(angle) * (radius * 1.3))
            cv2.circle(overlay, (px, py), int(np.random.uniform(4, 9)), (80, 220, 255), -1)

        glow = cv2.GaussianBlur(overlay, (25, 25), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, 0.6, 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def animate_butterfly_imaginal_discs(output_path: Path, duration: float = 7.0):
    base_img = load_and_fit_base_image(ASSETS_IMAGES / "butterfly_chrysalis_physical.jpg")
    total_frames = int(duration * VIDEO_FPS)
    frames = []
    h, w = base_img.shape[:2]

    for i in range(total_frames):
        t = i / VIDEO_FPS
        progress = i / total_frames
        zoom = 1.04 + progress * 0.08
        cur_w, cur_h = int(w / zoom), int(h / zoom)
        cx, cy = int(w * 0.5), int(h * 0.52)
        x1 = (w - cur_w) // 2
        y1 = max(0, min(h - cur_h, cy - cur_h // 2))
        crop = base_img[y1:y1 + cur_h, x1:x1 + cur_w]
        frame = cv2.resize(crop, (VIDEO_WIDTH, VIDEO_HEIGHT), interpolation=cv2.INTER_LINEAR)

        # Unfurling cellular growth glow: imaginal wing discs gently illuminating and expanding
        overlay = np.zeros_like(frame)
        grow_pulse = (math.sin(t * 2.5) + 1.0) / 2.0
        # Wing disc centers
        w_left = (int(VIDEO_WIDTH * 0.42), int(VIDEO_HEIGHT * 0.52))
        w_right = (int(VIDEO_WIDTH * 0.58), int(VIDEO_HEIGHT * 0.52))
        cv2.ellipse(overlay, w_left, (int(70 + grow_pulse * 30), int(120 + grow_pulse * 40)), -20, 0, 360, (140, 240, 255), -1)
        cv2.ellipse(overlay, w_right, (int(70 + grow_pulse * 30), int(120 + grow_pulse * 40)), 20, 0, 360, (140, 240, 255), -1)

        glow = cv2.GaussianBlur(overlay, (45, 45), 0)
        blended = cv2.addWeighted(frame, 1.0, glow, float(0.55 * (0.6 + grow_pulse * 0.4)), 0)
        frames.append(blended)

    save_and_transcode_frames(frames, output_path)

def render_all_physical_animations():
    animations = [
        ("jumping_spider_cephalothorax_hydraulic_pressure_pump.mp4", animate_spider_hydraulic_pump, 6.0),
        ("hydraulic_leg_extension_hemolymph_pressure_launch.mp4", animate_spider_hydraulic_launch, 7.0),
        ("chameleon_iridophore_photonic_crystal_lattice.mp4", animate_chameleon_iridophores, 6.0),
        ("chameleon_lattice_expansion_wavelength_shift.mp4", animate_chameleon_lattice_shift, 7.0),
        ("hummingbird_wing_figure_eight_aerodynamic_trajectory.mp4", animate_hummingbird_figure_eight, 6.0),
        ("leading_edge_vortex_dual_stroke_aerodynamic_lift.mp4", animate_hummingbird_vortex_lift, 7.0),
        ("woodpecker_cranial_biomechanics_shock_absorption.mp4", animate_woodpecker_cranial_shock, 6.0),
        ("woodpecker_hyoid_bone_hydraulic_seatbelt_skull.mp4", animate_woodpecker_hyoid_seatbelt, 7.0),
        ("owl_wing_serrated_comb_micro_turbulence_acoustic.mp4", animate_owl_comb_serrations, 6.0),
        ("owl_trailing_edge_acoustic_fringe_sound_cancellation.mp4", animate_owl_trailing_fringe, 7.0),
        ("jellyfish_cnidocyte_osmotic_capsule_pressure_mechanism.mp4", animate_jellyfish_cnidocyte, 6.0),
        ("nematocyst_harpoon_acceleration_five_million_g.mp4", animate_jellyfish_harpoon_launch, 7.0),
        ("caterpillar_digestive_autolysis_cellular_broth_chrysalis.mp4", animate_butterfly_autolysis, 6.0),
        ("imaginal_discs_stem_cell_organ_assembly_butterfly.mp4", animate_butterfly_imaginal_discs, 7.0)
    ]

    print(f"🎬 Rendering all {len(animations)} photorealistic physical 3D animations (ZERO graphs)...")
    t0 = time.time()
    for i, (fname, func, dur) in enumerate(animations):
        dest = ASSETS_VIDEOS / fname
        print(f"[{i+1}/{len(animations)}] Rendering '{fname}' ({dur}s)...")
        func(dest, duration=dur)
        print(f"   -> Saved: {dest} ({dest.stat().st_size / 1024:.1f} KB)")
    elapsed = time.time() - t0
    print(f"🎉 All 14 physical 3D animations rendered in {elapsed:.1f}s!")

if __name__ == "__main__":
    render_all_physical_animations()
