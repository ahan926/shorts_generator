"""
Batch Mechanism Video Generator
Renders 14 high-precision 1080x1920 30fps procedural scientific animations
for the 7 new YouTube Shorts.
"""
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

ASSETS_VIDEOS = Path("assets/videos")
ASSETS_VIDEOS.mkdir(parents=True, exist_ok=True)

def get_ffmpeg_binary() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    try:
        if mono:
            p = "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"
        elif bold:
            p = "C:/Windows/Fonts/segoeuib.ttf"
        else:
            p = "C:/Windows/Fonts/segoeui.ttf"
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    except Exception:
        pass
    return ImageFont.load_default()

def draw_hud_bracket(draw: ImageDraw.Draw, bbox: Tuple[int, int, int, int], color: Tuple[int, int, int], arm_len: int = 24, width: int = 2):
    x1, y1, x2, y2 = bbox
    draw.line([(x1, y1), (x1 + arm_len, y1)], fill=color, width=width)
    draw.line([(x1, y1), (x1, y1 + arm_len)], fill=color, width=width)
    draw.line([(x2, y1), (x2 - arm_len, y1)], fill=color, width=width)
    draw.line([(x2, y1), (x2, y1 + arm_len)], fill=color, width=width)
    draw.line([(x1, y2), (x1 + arm_len, y2)], fill=color, width=width)
    draw.line([(x1, y2), (x1, y2 - arm_len)], fill=color, width=width)
    draw.line([(x2, y2), (x2 + arm_len, y2)], fill=color, width=width)
    draw.line([(x2, y2), (x2, y2 - arm_len)], fill=color, width=width)

def save_and_transcode(frames: List[Image.Image], output_path: Path):
    temp_raw = output_path.with_suffix(".temp.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(str(temp_raw), fourcc, VIDEO_FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))
    for f in frames:
        np_frame = cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR)
        out_video.write(np_frame)
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
# 1. CHAMELEON ANIMATIONS
# -------------------------------------------------------------
def render_chameleon_iridophores(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(40, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        # Header
        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "CHAMELEON DERMAL OPTICS", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "SYSTEM: S-IRIDOPHORE PHOTONIC NANO-LATTICE", fill=(0, 210, 255), font=f_sub)

        # Main Diagram: Skin Layer Cutaway
        diag_bbox = (50, 220, VIDEO_WIDTH - 50, 880)
        d.rectangle(diag_bbox, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, diag_bbox, (0, 220, 255), 24, 2)
        d.text((80, 240), "[ANATOMICAL DERMAL CROSS-SECTION]", fill=(120, 180, 240), font=f_sub)

        # Layer 1: Epidermis (translucent)
        d.rectangle([80, 280, VIDEO_WIDTH - 80, 340], fill=(45, 65, 80), outline=(70, 100, 130), width=2)
        d.text((100, 298), "TRANSLUCENT EPIDERMIS (KERATIN SHIELD)", fill=(200, 225, 250), font=f_small)

        # Layer 2: Xanthophores (Yellow Pigment Cells)
        d.rectangle([80, 350, VIDEO_WIDTH - 80, 430], fill=(160, 140, 20), outline=(210, 185, 30), width=2)
        d.text((100, 375), "XANTHOPHORE LAYER: CAROTENOID PIGMENT (YELLOW FILTER)", fill=(255, 240, 150), font=f_small)

        # Layer 3: S-Iridophore Chamber (Photonic Crystals)
        d.rectangle([80, 440, VIDEO_WIDTH - 80, 850], fill=(15, 30, 50), outline=(0, 180, 240), width=2)
        d.text((100, 455), "S-IRIDOPHORE CELL: GUANINE PHOTONIC CRYSTALS", fill=(0, 230, 255), font=f_sub)

        # Draw Guanine Nanocrystal Hexagonal Grid
        cols, rows = 12, 6
        spacing_x, spacing_y = 65, 55
        start_x, start_y = 150, 510
        pulse = math.sin(t * 3.0) * 4
        for r in range(rows):
            for c in range(cols):
                cx = start_x + c * spacing_x + (r % 2) * (spacing_x // 2)
                cy = start_y + r * spacing_y
                cr = 16 + int(pulse)
                d.rectangle([cx - cr, cy - cr, cx + cr, cy + cr], fill=(0, 160, 220), outline=(120, 240, 255), width=2)

        # Incoming white light ray splitting into reflected blue wave
        d.line([(VIDEO_WIDTH // 2 - 120, 280), (VIDEO_WIDTH // 2, 510)], fill=(255, 255, 255), width=4)
        d.text((VIDEO_WIDTH // 2 - 180, 290), "SUNLIGHT (WHITE)", fill=(255, 255, 255), font=f_small)
        # Reflected blue beam
        d.line([(VIDEO_WIDTH // 2, 510), (VIDEO_WIDTH // 2 + 160, 280)], fill=(0, 200, 255), width=5)
        d.text((VIDEO_WIDTH // 2 + 110, 290), "REFLECTED (BLUE: 460nm)", fill=(0, 220, 255), font=f_small)

        # Telemetry Box
        tbox = (50, 920, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 940), "BIOPHYSICAL OPTICAL TELEMETRY", fill=(120, 180, 240), font=f_sub)
        metrics = [
            ("COLOR MECHANISM", "STRUCTURAL PHOTONIC INTERFERENCE (NOT PIGMENTS)"),
            ("CRYSTAL MATERIAL", "GUANINE NANO-PRISMS (REFRACTIVE INDEX n = 1.83)"),
            ("CRYSTAL GEOMETRY", "HEXAGONAL CLOSE-PACKED LATTICE (130nm)"),
            ("COLOR PRODUCTION", "REFLECTED BLUE LIGHT + YELLOW XANTHOPHORES = GREEN"),
            ("PIGMENT SPREAD MYTH", "DISPROVEN: CHROMATOPHORES DO NOT PUMP INK")
        ]
        for row_i, (k, v) in enumerate(metrics):
            ry = 990 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_chameleon_lattice_shift(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_big, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(48, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        progress = (math.sin(t * 1.5 - math.pi / 2) + 1.0) / 2.0 # 0.0 (relaxed) to 1.0 (excited)
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        # Header
        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "TUNABLE PHOTONIC BRAGG LATTICE", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "MECHANICAL DERMAL STRAIN & WAVELENGTH SHIFT", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Nanocrystal Spacing Dynamic
        box_mid = (50, 220, VIDEO_WIDTH - 50, 800)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[DYNAMIC CRYSTAL LATTICE SPACING SIMULATION]", fill=(120, 180, 240), font=f_sub)

        spacing_nm = 140 + progress * 90 # 140nm (blue) to 230nm (red)
        wave_lambda = 450 + progress * 230 # 450nm to 680nm
        # Color interpolation
        r_c = int(0 + progress * 255)
        g_c = int(210 * (1.0 - abs(progress - 0.4) * 2)) if abs(progress - 0.4) < 0.5 else 40
        b_c = int(255 * (1.0 - progress))
        active_color = (max(0, min(255, r_c)), max(0, min(255, g_c)), max(0, min(255, b_c)))

        # Draw expanding grid
        cols, rows = 8, 4
        base_sp = 50 + progress * 35
        start_x = (VIDEO_WIDTH - int((cols - 1) * base_sp)) // 2
        start_y = 360
        for r in range(rows):
            for c in range(cols):
                cx = start_x + int(c * base_sp)
                cy = start_y + int(r * base_sp)
                d.rectangle([cx - 14, cy - 14, cx + 14, cy + 14], fill=active_color, outline=(255, 255, 255), width=2)

        # Distance indicator arrow between two crystals
        c1x, c2x = start_x + int(3 * base_sp), start_x + int(4 * base_sp)
        ay = start_y + int(2 * base_sp) + 38
        d.line([(c1x, ay), (c2x, ay)], fill=(255, 220, 60), width=3)
        d.text((c1x - 10, ay + 8), f"LATTICE GAP: {spacing_nm:.0f} nm", fill=(255, 230, 80), font=f_small)

        # Reflected Sine Wave
        wave_pts = []
        for wx in range(80, VIDEO_WIDTH - 80, 4):
            wy = 680 + math.sin((wx * 0.04) / (0.6 + progress * 0.8) - t * 6) * 45
            wave_pts.append((wx, int(wy)))
        d.line(wave_pts, fill=active_color, width=5)
        d.text((80, 600), f"REFLECTED BRAGG WAVELENGTH: {wave_lambda:.0f} nm", fill=active_color, font=f_label)

        # Spectrum Bar HUD (Lower Box)
        sbox = (50, 840, VIDEO_WIDTH - 50, 1380)
        d.rectangle(sbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, sbox, (0, 220, 255), 20, 2)
        d.text((80, 860), "OPTICAL SPECTRUM WAVELENGTH INDICATOR", fill=(120, 180, 240), font=f_sub)

        # Draw visible spectrum gradient bar
        bar_x1, bar_y1, bar_x2, bar_y2 = 80, 920, VIDEO_WIDTH - 80, 980
        total_w = bar_x2 - bar_x1
        for px in range(total_w):
            frac = px / total_w
            # approx rainbow spectrum from 400nm (violet) to 700nm (red)
            if frac < 0.2: sc = (80, 0, 180)
            elif frac < 0.4: sc = (0, 120, 255)
            elif frac < 0.6: sc = (0, 220, 80)
            elif frac < 0.8: sc = (240, 200, 0)
            else: sc = (255, 40, 40)
            d.line([(bar_x1 + px, bar_y1), (bar_x1 + px, bar_y2)], fill=sc, width=1)
        d.rectangle([bar_x1, bar_y1, bar_x2, bar_y2], outline=(255, 255, 255), width=2)

        # Spectrum cursor pointer
        cur_x = int(bar_x1 + ((wave_lambda - 420) / 280) * total_w)
        d.polygon([(cur_x, bar_y1 - 15), (cur_x - 12, bar_y1 - 32), (cur_x + 12, bar_y1 - 32)], fill=(255, 255, 255))
        d.polygon([(cur_x, bar_y2 + 15), (cur_x - 12, bar_y2 + 32), (cur_x + 12, bar_y2 + 32)], fill=(255, 255, 255))

        # Status text
        st_title = "STATE: RELAXED (CRYSTALS PACKED)" if progress < 0.5 else "STATE: EXCITED / STRESSED (LATTICE STRETCHED)"
        st_desc = "460nm BLUE REFLECTED + YELLOW PIGMENT -> VIBRANT GREEN" if progress < 0.5 else "LATTICE SPREADS -> DIRECT REFLECTION OF RED & ORANGE"
        d.text((80, 1030), st_title, fill=(255, 255, 255), font=f_label)
        d.text((80, 1080), st_desc, fill=active_color, font=f_sub)

        bullets = [
            f"Current Lattice Spacing: {spacing_nm:.1f} nm (+{progress*100:.0f}% expanded)",
            f"Peak Reflected Light: λ = {wave_lambda:.1f} nm",
            "Speed: Rapid mechanical muscular relaxation in dermal layer",
            "Combat / Mating Display: Shifts instantly from camouflage to warning"
        ]
        for b_i, b_t in enumerate(bullets):
            d.text((80, 1140 + b_i * 45), f"• {b_t}", fill=(200, 220, 245), font=f_small)

        frames.append(img)
    save_and_transcode(frames, output_path)

# -------------------------------------------------------------
# 2. HUMMINGBIRD ANIMATIONS
# -------------------------------------------------------------
def render_hummingbird_figure_eight(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_big, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(52, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "HUMMINGBIRD FLIGHT KINEMATICS", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "SYSTEM: 180° REVERSE FIGURE-8 DUAL ROTOR", fill=(0, 210, 255), font=f_sub)

        # Center Figure-8 Trajectory Display
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[3D WINGTIP TRAJECTORY & 180° INVERSION]", fill=(120, 180, 240), font=f_sub)

        # Draw complete Figure-8 path
        center_x, center_y = VIDEO_WIDTH // 2, 520
        scale_x, scale_y = 360, 160
        path_pts = []
        for theta_deg in range(0, 360, 3):
            rad = math.radians(theta_deg)
            px = center_x + math.sin(rad) * scale_x
            py = center_y + math.sin(rad * 2) * scale_y * 0.7
            path_pts.append((px, py))
        d.line(path_pts + [path_pts[0]], fill=(35, 75, 110), width=4)

        # Active wingtip position
        stroke_angle = (t * 4.0 * math.pi) % (2 * math.pi)
        curr_x = center_x + math.sin(stroke_angle) * scale_x
        curr_y = center_y + math.sin(stroke_angle * 2) * scale_y * 0.7
        is_forward = math.cos(stroke_angle) > 0 # Downstroke vs Upstroke

        # Wing vector from center bird body
        body_x, body_y = center_x, center_y + 40
        d.ellipse([body_x - 20, body_y - 30, body_x + 20, body_y + 30], fill=(0, 200, 140), outline=(255, 255, 255), width=2)
        d.line([(body_x, body_y), (int(curr_x), int(curr_y))], fill=(0, 220, 255), width=8)

        # Wing foil cross-section angle (inverts 180 deg)
        foil_angle = 20 if is_forward else 160
        frad = math.radians(foil_angle)
        fx1 = int(curr_x - math.cos(frad) * 50)
        fy1 = int(curr_y - math.sin(frad) * 50)
        fx2 = int(curr_x + math.cos(frad) * 50)
        fy2 = int(curr_y + math.sin(frad) * 50)
        d.line([(fx1, fy1), (fx2, fy2)], fill=(255, 220, 60), width=10)
        d.ellipse([int(curr_x) - 12, int(curr_y) - 12, int(curr_x) + 12, int(curr_y) + 12], fill=(255, 255, 255))

        phase_txt = "FORWARD DOWNSTROKE: NORMAL CHORD (+75% LIFT)" if is_forward else "BACKWARD UPSTROKE: 180° INVERTED CHORD (+25% LIFT)"
        d.text((80, 750), phase_txt, fill=(0, 255, 180) if is_forward else (255, 200, 50), font=f_label)

        # Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "AERODYNAMIC FLIGHT TELEMETRY", fill=(120, 180, 240), font=f_sub)
        metrics = [
            ("WING FLAP FREQUENCY", "80 Hz (80 FULL CYCLES PER SECOND)"),
            ("SHOULDER FLEXIBILITY", "BALL-AND-SOCKET JOINT PERMITS 180° INVERSION"),
            ("AERODYNAMIC STROKE", "HORIZONTAL FIGURE-EIGHT (HELICOPTER ROTOR PROFILE)"),
            ("LIFT DISTRIBUTION", "75% FORWARD DOWNSTROKE / 25% INVERTED UPSTROKE"),
            ("FLIGHT VECTOR CAPABILITY", "STATIONARY HOVER, BACKWARD FLIGHT, INVERTED DIVE")
        ]
        for row_i, (k, v) in enumerate(metrics):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_hummingbird_vortex_lift(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "LEADING-EDGE VORTEX & DUAL LIFT", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "MECHANICAL SUCTION CORE GENERATES 100% HOVER", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Airfoil & Vortex Formation
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[AERODYNAMIC STREAMLINE & VORTEX PRESSURE CORE]", fill=(120, 180, 240), font=f_sub)

        # Wing foil in cross section
        foil_pts = [
            (250, 520), (320, 490), (450, 485), (650, 510), (750, 525),
            (650, 535), (450, 545), (320, 545), (250, 520)
        ]
        d.polygon(foil_pts, fill=(50, 120, 180), outline=(120, 220, 255))
        d.text((450, 560), "INVERTIBLE AIRFOIL", fill=(140, 190, 240), font=f_small)

        # Swirling Leading-Edge Vortex (LEV) over wing
        vx, vy = 350, 420
        d.text((vx - 60, vy - 100), "LOW PRESSURE SUCTION VORTEX", fill=(0, 255, 255), font=f_small)
        # Dynamic spiral rings
        for ring_i in range(5):
            radius = 25 + ring_i * 18
            start_ang = int((t * 360 * 2 + ring_i * 45) % 360)
            d.arc([vx - radius, vy - radius, vx + radius, vy + radius], start=start_ang, end=start_ang + 240, fill=(0, 255, 200), width=3)
        # Upward Lift Arrow
        d.line([(500, 460), (500, 280)], fill=(0, 255, 120), width=8)
        d.polygon([(500, 260), (480, 290), (520, 290)], fill=(0, 255, 120))
        d.text((530, 340), "CONTINUOUS LIFT VECTOR", fill=(0, 255, 120), font=f_label)

        # Lower Box: Lift Comparison Bar Gauges
        lbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(lbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, lbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "LIFT GENERATION COMPARISON (HUMMINGBIRD vs NORMAL BIRDS)", fill=(120, 180, 240), font=f_sub)

        # Gauge 1: Hummingbird Downstroke (75%)
        d.text((80, 930), "HUMMINGBIRD FORWARD DOWNSTROKE: +75% LIFT", fill=(200, 225, 255), font=f_small)
        d.rectangle([80, 960, VIDEO_WIDTH - 80, 1000], fill=(15, 30, 45), outline=(40, 80, 120), width=2)
        d.rectangle([82, 962, int(82 + (VIDEO_WIDTH - 164) * 0.75), 998], fill=(0, 220, 255))

        # Gauge 2: Hummingbird Inverted Upstroke (25%)
        d.text((80, 1020), "HUMMINGBIRD INVERTED UPSTROKE: +25% LIFT (ACTIVE ROTOR)", fill=(255, 220, 80), font=f_small)
        d.rectangle([80, 1050, VIDEO_WIDTH - 80, 1090], fill=(15, 30, 45), outline=(40, 80, 120), width=2)
        d.rectangle([82, 1052, int(82 + (VIDEO_WIDTH - 164) * 0.25), 1088], fill=(255, 210, 60))

        # Gauge 3: Typical Songbird Upstroke (0% Lift - Feather Recovery)
        d.text((80, 1110), "TYPICAL BIRD UPSTROKE: 0% LIFT (PASSIVE RETURN)", fill=(160, 170, 180), font=f_small)
        d.rectangle([80, 1140, VIDEO_WIDTH - 80, 1180], fill=(15, 30, 45), outline=(40, 80, 120), width=2)
        d.text((100, 1150), "[ZERO AERODYNAMIC LIFT GENERATED]", fill=(120, 130, 140), font=f_small)

        # Summary bullets
        d.text((80, 1220), "• Dual-stroke lift maintains perfect motionless hover in mid-air", fill=(220, 235, 250), font=f_small)
        d.text((80, 1260), "• Leading-edge vortex does not detach, creating steady suction", fill=(220, 235, 250), font=f_small)
        d.text((80, 1300), "• Oxygen consumption: 10x higher per gram than Olympic athletes", fill=(220, 235, 250), font=f_small)

        frames.append(img)
    save_and_transcode(frames, output_path)

# -------------------------------------------------------------
# 3. WOODPECKER ANIMATIONS
# -------------------------------------------------------------
def render_woodpecker_cranial_shock(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "WOODPECKER CRANIAL DECELERATION", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "BIOMECHANICS: 1,200 G IMPACT SHIELD SYSTEM", fill=(0, 210, 255), font=f_sub)

        # Center Skull Diagram
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[ANATOMICAL SKULL IMPACT PROFILE & ASYMMETRY]", fill=(120, 180, 240), font=f_sub)

        # Tree bark vertical barrier on left
        d.rectangle([80, 320, 160, 750], fill=(70, 50, 35), outline=(130, 95, 65), width=2)
        d.text((90, 510), "BARK", fill=(200, 180, 150), font=f_small)

        # Strike impact animation cycle
        strike_phase = math.sin(t * 8.0)
        beak_x = 160 if strike_phase > 0.8 else 185
        # Beak drawing
        # Lower beak longer
        d.polygon([(beak_x, 520), (beak_x + 220, 545), (beak_x + 220, 515)], fill=(180, 190, 205), outline=(255, 255, 255))
        d.polygon([(beak_x + 10, 495), (beak_x + 220, 515), (beak_x + 220, 485)], fill=(150, 160, 175), outline=(220, 220, 220))

        # Skull and brain chamber
        sx, sy = beak_x + 220, 500
        d.ellipse([sx, sy - 140, sx + 320, sy + 140], fill=(25, 45, 70), outline=(0, 180, 240), width=3)
        # Brain inside skull (tight CSF space)
        d.ellipse([sx + 80, sy - 80, sx + 250, sy + 70], fill=(220, 80, 100), outline=(255, 140, 160), width=2)
        d.text((sx + 115, sy - 15), "BRAIN", fill=(255, 255, 255), font=f_label)

        # Spongy trabecular bone region in frontal skull
        for b_r in range(5):
            for b_c in range(4):
                bx = sx + 20 + b_c * 15
                by = sy - 40 + b_r * 20
                d.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(0, 230, 255))
        d.text((sx - 20, sy - 160), "TRABECULAR SPONGY BONE (SHOCK DAMPENER)", fill=(0, 230, 255), font=f_small)

        # Impact Deceleration Vector Arrow
        if strike_phase > 0.8:
            d.line([(beak_x, 515), (beak_x + 100, 515)], fill=(255, 50, 50), width=8)
            d.text((beak_x + 20, 450), "1,200 G DECELERATION!", fill=(255, 60, 60), font=f_label)

        # Lower Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "CRANIAL BIOMECHANICS & ACCELEROMETRY", fill=(120, 180, 240), font=f_sub)
        metrics = [
            ("IMPACT FORCE", "1,200 Gs (HUMANS EXPERIENCE SEVERE CONCUSSION AT 80-100 Gs)"),
            ("PECKING FREQUENCY", "20 STRIKES PER SECOND (6.0 m/s IMPACT VELOCITY)"),
            ("BEAK ASYMMETRY", "LOWER BEAK EXTENSION DEFLECTS 60% FORCE INTO STERNUM"),
            ("CSF CLEARANCE", "TIGHT ZERO-SLOSH FLUID BUFFER PREVENTS ROTATIONAL SHEAR"),
            ("CONCUSSION RESISTANCE", "MICRO-POROUS BONE STRUCTURE DISSIPATES ENERGY")
        ]
        for row_i, (k, v) in enumerate(metrics):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_woodpecker_hyoid_seatbelt(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "HYOID BONE CRANIAL SEATBELT", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "ANATOMICAL HYDRAULIC RESTRAINT SLING", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Hyoid bone wrapping around the entire skull
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[360-DEGREE CRANIAL HYOID SLING ANATOMY]", fill=(120, 180, 240), font=f_sub)

        # Skull base center
        sk_cx, sk_cy = VIDEO_WIDTH // 2, 530
        d.ellipse([sk_cx - 180, sk_cy - 150, sk_cx + 180, sk_cy + 150], fill=(20, 35, 55), outline=(50, 90, 130), width=3)
        # Beak pointing right
        d.polygon([(sk_cx + 160, sk_cy - 20), (sk_cx + 340, sk_cy + 10), (sk_cx + 160, sk_cy + 30)], fill=(80, 100, 120))

        # Hyoid Bone: Wraps from under jaw (bottom), around back of head, over top, into right nostril!
        hyoid_pts = [
            (sk_cx + 80, sk_cy + 120),   # Under beak/throat
            (sk_cx - 20, sk_cy + 160),   # Throat junction
            (sk_cx - 190, sk_cy + 110),  # Under occiput
            (sk_cx - 220, sk_cy),        # Behind back of skull
            (sk_cx - 180, sk_cy - 140),  # Upper rear skull
            (sk_cx - 20, sk_cy - 190),   # Over skull vertex (top)
            (sk_cx + 140, sk_cy - 140),  # Down forehead
            (sk_cx + 200, sk_cy - 50)    # Anchors into nostril!
        ]
        # Pulsing tension on impact
        tension_width = 8 + int(math.sin(t * 6.0) * 3)
        d.line(hyoid_pts, fill=(255, 210, 40), width=tension_width)
        for hp in hyoid_pts:
            d.ellipse([hp[0] - 8, hp[1] - 8, hp[0] + 8, hp[1] + 8], fill=(255, 255, 255))
        d.text((sk_cx - 160, sk_cy - 225), "HYOID HORN SLING (WRAPS OVER HEAD)", fill=(255, 220, 60), font=f_label)
        d.text((sk_cx + 180, sk_cy - 85), "ANCHORS INTO NOSTRIL", fill=(0, 220, 255), font=f_small)

        # Oscilloscope vibration damping trace
        d.rectangle([80, 710, VIDEO_WIDTH - 80, 790], fill=(8, 15, 25), outline=(0, 180, 220), width=1)
        d.text((90, 720), "CRANIAL VIBRATION OSCILLOSCOPE DAMPING TRACE:", fill=(0, 220, 255), font=f_small)
        osc_pts = []
        for ox in range(90, VIDEO_WIDTH - 90, 4):
            frac = (ox - 90) / (VIDEO_WIDTH - 180)
            oy = 755 + math.exp(-frac * 5.0) * math.sin(frac * 35.0 - t * 8.0) * 25
            osc_pts.append((ox, int(oy)))
        d.line(osc_pts, fill=(0, 255, 160), width=2)

        # Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "BIOLOGICAL CRANIAL SUSPENSION TELEMETRY", fill=(120, 180, 240), font=f_sub)
        bullets = [
            ("ANATOMICAL ROUTING", "BRANCHES FROM JAW, LOOPS OVER SKULL, ENTERS RIGHT NOSTRIL"),
            ("TENSION RESPONSE", "CONTRACTS LIKE A RIGID SEATBELT TO ANCHOR SKULL IN LINE"),
            ("SHEAR ELIMINATION", "PREVENTS ROTATIONAL TWISTING OF THE BRAINSTEM"),
            ("ENERGY DISSIPATION", "VIBRATIONS DECAY WITHIN 1.5 MILLISECONDS"),
            ("CONCUSSION STATUS", "ZERO TRAUMATIC BRAIN INJURY (PERFECT BIOLOGICAL ARMOR)")
        ]
        for row_i, (k, v) in enumerate(bullets):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

# -------------------------------------------------------------
# 4. OWL ANIMATIONS
# -------------------------------------------------------------
def render_owl_serrated_comb(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "OWL ACOUSTIC STEALTH FLIGHT", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "SYSTEM: LEADING-EDGE SERRATED SERRATIONS", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Serrated Comb Micro-turbulences
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[LEADING-EDGE MICRO-SERRATION FLUID DYNAMICS]", fill=(120, 180, 240), font=f_sub)

        # Flight feather main shaft
        d.line([(VIDEO_WIDTH // 2 - 180, 320), (VIDEO_WIDTH // 2 - 180, 750)], fill=(200, 220, 240), width=12)
        d.text((VIDEO_WIDTH // 2 - 280, 340), "FEATHER RACHIS", fill=(140, 180, 220), font=f_small)

        # Comb-like Serrations (stiff teeth pointing into incoming airflow)
        teeth_count = 14
        for ti in range(teeth_count):
            ty = 360 + ti * 26
            # Teeth pointing left
            d.polygon([
                (VIDEO_WIDTH // 2 - 180, ty),
                (VIDEO_WIDTH // 2 - 270, ty + 8),
                (VIDEO_WIDTH // 2 - 180, ty + 16)
            ], fill=(255, 220, 80), outline=(255, 255, 255))

        # Airflow particles: incoming smooth air broken into micro-eddies
        for flow_i in range(8):
            fy = 370 + flow_i * 45
            # Incoming streamline
            d.line([(80, fy), (VIDEO_WIDTH // 2 - 260, fy)], fill=(0, 200, 255), width=3)
            # Micro-eddies behind teeth
            eddy_x = VIDEO_WIDTH // 2 - 100 + int(math.sin(t * 8.0 + flow_i) * 30)
            d.arc([eddy_x - 18, fy - 18, eddy_x + 18, fy + 18], start=0, end=300, fill=(0, 255, 180), width=2)

        d.text((80, 330), "INCOMING AIRFLOW", fill=(0, 210, 255), font=f_small)
        d.text((VIDEO_WIDTH // 2 - 80, 480), "BREAKS MACRO-VORTICES INTO INAUDIBLE MICRO-EDDIES", fill=(0, 255, 180), font=f_label)

        # Lower Box: Decibel Comparison
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "ACOUSTIC DECIBEL COMPARISON IN FLIGHT", fill=(120, 180, 240), font=f_sub)

        # Pigeon (65 dB)
        d.text((80, 930), "PIGEON FLIGHT TURBULENCE: ~65 dB (LOUD AUDIBLE FLAPPING)", fill=(240, 120, 120), font=f_small)
        d.rectangle([80, 960, VIDEO_WIDTH - 80, 995], fill=(20, 30, 45), outline=(60, 80, 100), width=1)
        d.rectangle([82, 962, int(82 + (VIDEO_WIDTH - 164) * 0.75), 993], fill=(240, 80, 80))

        # Barn Owl (< 15 dB)
        d.text((80, 1020), "BARN OWL STEALTH GLIDE: < 15 dB (BELOW AUDIBLE THRESHOLD)", fill=(0, 255, 140), font=f_small)
        d.rectangle([80, 1050, VIDEO_WIDTH - 80, 1085], fill=(20, 30, 45), outline=(60, 80, 100), width=1)
        d.rectangle([82, 1052, int(82 + (VIDEO_WIDTH - 164) * 0.12), 1083], fill=(0, 255, 140))

        bullets = [
            "Leading-edge comb teeth break single roaring vortex into thousands of tiny ripples",
            "Acoustic frequency shifted above 20 kHz (inaudible to mammalian prey)",
            "Enables owls to hunt in complete pitch-black darkness by sound alone"
        ]
        for b_i, b_t in enumerate(bullets):
            d.text((80, 1140 + b_i * 60), f"• {b_t}", fill=(200, 225, 250), font=f_small)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_owl_trailing_fringe(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "TRAILING-EDGE FRINGE & VELVET DOWN", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "SOUND ABSORPTION & VORTEX SHEDDING CANCELLATION", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Trailing Edge & Downy Velvet
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[POROUS ACOUSTIC VELVET & ELASTIC FRINGE MESH]", fill=(120, 180, 240), font=f_sub)

        # Wing profile
        d.polygon([(180, 480), (450, 430), (750, 500), (450, 540)], fill=(40, 70, 100), outline=(100, 180, 240))
        d.text((360, 470), "WING MEMBRANE", fill=(200, 225, 250), font=f_small)

        # Velvet down coating (top layer absorbs sound)
        for vx in range(220, 700, 20):
            vy = 445 if vx < 450 else 470
            d.line([(vx, vy), (vx - 5, vy - 25)], fill=(0, 220, 255), width=2)
        d.text((280, 380), "VELVET DOWN (ABSORBS HIGH-FREQUENCY SOUND)", fill=(0, 220, 255), font=f_small)

        # Trailing Edge Flexible Fringe (filaments extending off back edge)
        for fx in range(700, 920, 12):
            fy = 500 + int(math.sin(t * 7.0 + fx * 0.1) * 8)
            d.line([(750, 500), (fx + 40, fy + (fx - 700) // 4)], fill=(255, 220, 80), width=2)
        d.text((620, 570), "TRAILING-EDGE FRINGE", fill=(255, 220, 80), font=f_label)
        d.text((620, 610), "ELIMINATES VORTEX SHEDDING NOISE", fill=(200, 230, 255), font=f_small)

        # Lower Box: Acoustic Frequency Response
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "AERODYNAMIC STEALTH TRIAD METRICS", fill=(120, 180, 240), font=f_sub)
        bullets = [
            ("MECHANISM 1 (FRONT)", "SERRATED LEADING COMB: BREAKS AIR INTO MICRO-TURBULENCES"),
            ("MECHANISM 2 (SURFACE)", "POROUS VELVET DOWN: DAMPENS SOUND WAVES LIKE ACOUSTIC FOAM"),
            ("MECHANISM 3 (REAR)", "FLEXIBLE FRINGE: SMOOTHS AIRFLOW EXIT, PREVENTING SHED NOISE"),
            ("AUDITORY ADVANTAGE", "SURPRISE PREY BEFORE SOUND WAVES REACH RODENT EARS"),
            ("WIND NOISE ELIMINATION", "OWLS HEAR PREY FOOTSTEPS BENEATH 2 FEET OF SNOW")
        ]
        for row_i, (k, v) in enumerate(bullets):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

# -------------------------------------------------------------
# 5. JELLYFISH ANIMATIONS
# -------------------------------------------------------------
def render_jellyfish_cnidocyte_capsule(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "JELLYFISH CNIDOCYTE CANNON", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "SYSTEM: 150 ATMOSPHERE OSMOTIC PRESSURE CAPSULE", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Cnidocyte Cell & Pressurized Nematocyst
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[ANATOMICAL CNIDOCYTE INTERNAL CROSS-SECTION]", fill=(120, 180, 240), font=f_sub)

        # Outer cnidocyte cell body
        d.ellipse([VIDEO_WIDTH // 2 - 240, 320, VIDEO_WIDTH // 2 + 240, 760], fill=(18, 35, 60), outline=(0, 180, 240), width=3)
        d.text((VIDEO_WIDTH // 2 - 120, 340), "CNIDOCYTE STINGING CELL", fill=(140, 200, 255), font=f_small)

        # Inner collagenous pressurized capsule (nematocyst)
        capsule_pts = [
            (VIDEO_WIDTH // 2 - 150, 420), (VIDEO_WIDTH // 2 + 150, 420),
            (VIDEO_WIDTH // 2 + 160, 680), (VIDEO_WIDTH // 2 - 160, 680)
        ]
        d.polygon(capsule_pts, fill=(35, 25, 65), outline=(220, 100, 255), width=3)
        d.text((VIDEO_WIDTH // 2 - 140, 640), "NEMATOCYST CAPSULE (150 ATM)", fill=(240, 140, 255), font=f_small)

        # Coiled spring harpoon tubule inside
        coil_pts = []
        for cy in range(460, 620, 8):
            cx = VIDEO_WIDTH // 2 + int(math.sin(cy * 0.2 + t * 4.0) * 80)
            coil_pts.append((cx, cy))
        d.line(coil_pts, fill=(255, 220, 60), width=5)
        d.text((VIDEO_WIDTH // 2 - 90, 520), "INVERTED HARPOON", fill=(255, 220, 80), font=f_label)

        # Sensory cnidocil trigger hair at the top
        d.line([(VIDEO_WIDTH // 2, 320), (VIDEO_WIDTH // 2 + 20, 260)], fill=(0, 255, 180), width=6)
        d.text((VIDEO_WIDTH // 2 + 35, 265), "CNIDOCIL TRIGGER HAIR", fill=(0, 255, 180), font=f_small)

        # Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "CELLULAR BIOPHYSICAL PRESSURE TELEMETRY", fill=(120, 180, 240), font=f_sub)
        metrics = [
            ("INTERNAL PRESSURE", "150 ATMOSPHERES (15 MPa / HIGHER THAN SCUBA TANKS)"),
            ("DRIVING MECHANISM", "HIGHLY DENSE POLY-GAMMA-GLUTAMATE OSMOTIC PUMP"),
            ("ENERGY STORAGE", "ELASTIC STRAIN PRE-LOADED IN COLLAGENOUS CAPSULE WALL"),
            ("TRIGGER SENSITIVITY", "DUAL CHEMICAL (MUCUS) & MECHANICAL HAIR CONTACT"),
            ("FIRING SPEED", "EXPLOSIVE INVERSION IN SUB-MICROSECOND TIMEFRAME")
        ]
        for row_i, (k, v) in enumerate(metrics):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_nematocyst_harpoon_acceleration(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_big, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(52, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "5-MILLION G HARPOON ACCELERATION", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "FASTEST BIOLOGICAL MECHANISM IN THE ANIMAL KINGDOM", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Explosive Inversion & Target Penetration
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[HIGH-SPEED INVERSION & VENOM DELIVERY STYLET]", fill=(120, 180, 240), font=f_sub)

        # Capsule base at bottom
        d.rectangle([VIDEO_WIDTH // 2 - 120, 680, VIDEO_WIDTH // 2 + 120, 780], fill=(45, 30, 80), outline=(220, 100, 255), width=2)

        # Ejected Shaft / Harpoon
        shaft_top = 340
        d.line([(VIDEO_WIDTH // 2, 680), (VIDEO_WIDTH // 2, shaft_top)], fill=(255, 220, 60), width=12)

        # Barbed Stylet Head (penetrating prey cuticle)
        head_pts = [
            (VIDEO_WIDTH // 2, shaft_top - 60),
            (VIDEO_WIDTH // 2 - 40, shaft_top),
            (VIDEO_WIDTH // 2, shaft_top - 20),
            (VIDEO_WIDTH // 2 + 40, shaft_top)
        ]
        d.polygon(head_pts, fill=(255, 50, 50), outline=(255, 255, 255))
        # Reverse barbs
        for b_y in [shaft_top + 30, shaft_top + 80, shaft_top + 130]:
            d.line([(VIDEO_WIDTH // 2 - 35, b_y + 20), (VIDEO_WIDTH // 2, b_y)], fill=(255, 200, 50), width=5)
            d.line([(VIDEO_WIDTH // 2 + 35, b_y + 20), (VIDEO_WIDTH // 2, b_y)], fill=(255, 200, 50), width=5)

        # Venom delivery spray pulses
        d.text((VIDEO_WIDTH // 2 - 160, 270), "PREY CUTICLE PENETRATED!", fill=(255, 80, 80), font=f_label)
        pulse_r = int((t * 200) % 80)
        d.arc([VIDEO_WIDTH // 2 - pulse_r, shaft_top - 60 - pulse_r, VIDEO_WIDTH // 2 + pulse_r, shaft_top - 60 + pulse_r], start=180, end=360, fill=(0, 255, 200), width=3)

        # Lower Box: Ballistic Telemetry
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "EXTREME BIOMECHANICAL BALLISTICS", fill=(120, 180, 240), font=f_sub)
        bullets = [
            ("DECELERATION / LAUNCH", "5,410,000 Gs OF PEAK ACCELERATION"),
            ("DISCHARGE DURATION", "700 NANOSECONDS (LESS THAN 1 MILLIONTH OF A SECOND)"),
            ("VELOCITY", "37 METERS PER SECOND (OVER 130 KM/H OUT OF A CELL)"),
            ("PENETRATION FORCE", "SUFFICIENT TO DRILL THROUGH HARD CRUSTACEAN CARAPACES"),
            ("TOXIN INJECTION", "HOLLOW TUBULE SQUIRTS NEUROTOXINS DIRECTLY INTO BLOODSTREAM")
        ]
        for row_i, (k, v) in enumerate(bullets):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

# -------------------------------------------------------------
# 6. BUTTERFLY METAMORPHOSIS ANIMATIONS
# -------------------------------------------------------------
def render_butterfly_autolysis(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "METAMORPHIC AUTOLYSIS SOUP", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "SYSTEM: ENZYMATIC DECONSTRUCTION OF CATERPILLAR", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Chrysalis Cutaway Dissolving
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[CHRYSALIS CUTAWAY & CASPASE DIGESTION BROTH]", fill=(120, 180, 240), font=f_sub)

        # Chrysalis exterior pod outline
        ch_pts = [
            (VIDEO_WIDTH // 2, 290), (VIDEO_WIDTH // 2 + 180, 380),
            (VIDEO_WIDTH // 2 + 190, 620), (VIDEO_WIDTH // 2 + 60, 760),
            (VIDEO_WIDTH // 2 - 60, 760), (VIDEO_WIDTH // 2 - 190, 620),
            (VIDEO_WIDTH // 2 - 180, 380)
        ]
        d.polygon(ch_pts, fill=(25, 45, 30), outline=(50, 140, 70), width=3)

        # Liquid soup interior level
        soup_y = 420
        d.rectangle([VIDEO_WIDTH // 2 - 150, soup_y, VIDEO_WIDTH // 2 + 150, 740], fill=(110, 95, 25, 200))
        d.text((VIDEO_WIDTH // 2 - 130, soup_y + 40), "ENZYMATIC NUTRIENT SOUP", fill=(255, 240, 120), font=f_label)

        # Dissolving particles (autolysis bubbles)
        for bi in range(16):
            bx = VIDEO_WIDTH // 2 - 120 + (bi * 17) % 240
            by = soup_y + 60 + int((bi * 23 + t * 40) % 240)
            d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=(240, 220, 100), outline=(255, 255, 255))

        d.text((VIDEO_WIDTH // 2 - 140, 700), "CASPASE ENZYMES ACTIVATED", fill=(255, 120, 80), font=f_small)

        # Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "CELLULAR LYSIS & CHEMICAL RECYCLING METRICS", fill=(120, 180, 240), font=f_sub)
        bullets = [
            ("AUTOLYSIS PROCESS", "CATERPILLAR DISSOLVES ITS OWN MUSCLES, GUT & ORGANS"),
            ("LYSIS ENZYMES", "CASPASES & CATHEPSINS TRIGGER PROGRAMMED CELL DEATH"),
            ("RESULTING MEDIUM", "NUTRIENT-RICH SOUP OF AMINO ACIDS, LIPIDS & PROTEINS"),
            ("PRESERVED STRUCTURES", "DORMANT STEM CELL CLUSTERS CALLED IMAGINAL DISCS SURVIVE"),
            ("BIOLOGICAL FACT", "THE CATERPILLAR IS ESSENTIALLY LIQUEFIED ALIVE")
        ]
        for row_i, (k, v) in enumerate(bullets):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_butterfly_imaginal_discs(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "IMAGINAL DISC MORPHOGENESIS", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "STEM CELL CLUSTERS CONSUME BROTH TO BUILD BUTTERFLY", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Imaginal Discs Assembling Butterfly Structures
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[IMAGINAL DISC CLUSTER DIFFERENTIATION & ASSEMBLY]", fill=(120, 180, 240), font=f_sub)

        # Discs expanding and forming wings
        cx, cy = VIDEO_WIDTH // 2, 520
        # Wing Discs (expanding left and right)
        wing_w = int(120 + math.sin(t * 2.0) * 30)
        wing_h = int(180 + math.sin(t * 2.0) * 20)
        # Left Wing
        d.ellipse([cx - 30 - wing_w, cy - wing_h, cx - 10, cy + wing_h // 2], fill=(0, 160, 220), outline=(255, 255, 255), width=3)
        # Right Wing
        d.ellipse([cx + 10, cy - wing_h, cx + 30 + wing_w, cy + wing_h // 2], fill=(0, 160, 220), outline=(255, 255, 255), width=3)
        d.text((cx - 100, cy - wing_h - 40), "WING IMAGINAL DISCS", fill=(0, 230, 255), font=f_label)

        # Eye and Antenna Discs (Top)
        d.ellipse([cx - 45, cy - wing_h + 10, cx - 15, cy - wing_h + 40], fill=(255, 210, 60))
        d.ellipse([cx + 15, cy - wing_h + 10, cx + 45, cy - wing_h + 40], fill=(255, 210, 60))
        d.text((cx + 60, cy - wing_h + 15), "COMPOUND EYE DISCS", fill=(255, 220, 80), font=f_small)

        # Leg Discs (Bottom)
        for li in range(3):
            lx = cx - 50 + li * 50
            d.line([(lx, cy + 40), (lx - 20, cy + 120), (lx, cy + 160)], fill=(0, 255, 160), width=4)
        d.text((cx - 80, cy + 180), "LEG IMAGINAL DISCS", fill=(0, 255, 160), font=f_small)

        # Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "METAMORPHIC RECONSTRUCTION TELEMETRY", fill=(120, 180, 240), font=f_sub)
        bullets = [
            ("IMAGINAL DISC COUNT", "PRECISELY 6 PAIRS DORMANT IN CATERPILLAR SINCE BIRTH"),
            ("DEVELOPMENTAL ROLES", "DEDICATED DISCS SPECIFICALLY CODE FOR WINGS, LEGS, EYES & ANTENNAE"),
            ("NUTRIENT SOURCE", "DISCS CONSUME SURROUNDING LIQUEFIED CATERPILLAR BROTH"),
            ("MEMORY RETENTION", "SCIENTIFIC EVIDENCE PROVES ADULT BUTTERFLIES RETAIN CATERPILLAR MEMORIES"),
            ("FINAL METAMORPHOSIS", "PUMPS HEMOLYMPH TO EXPAND WINGS UPON EMERGENCE")
        ]
        for row_i, (k, v) in enumerate(bullets):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

# -------------------------------------------------------------
# 7. JUMPING SPIDER ANIMATIONS
# -------------------------------------------------------------
def render_spider_hydraulic_pump(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "SPIDER HYDRAULIC PUMP SYSTEM", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "SYSTEM: CEPHALOTHORAX HEMOLYMPH HIGH-PRESSURE PULSE", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Cephalothorax Cross-Section
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[PROSOMA HYDRAULIC CHAMBER & MUSCLE CONTRACTION]", fill=(120, 180, 240), font=f_sub)

        # Cephalothorax Carapace
        cx, cy = VIDEO_WIDTH // 2, 520
        d.ellipse([cx - 220, cy - 160, cx + 220, cy + 160], fill=(25, 40, 60), outline=(0, 180, 240), width=3)
        d.text((cx - 150, cy - 140), "CEPHALOTHORAX (PROSOMA)", fill=(120, 180, 240), font=f_small)

        # Internal oblique muscles squeezing the chamber
        squeeze = int(math.sin(t * 5.0) * 15)
        d.line([(cx - 140, cy - 80 + squeeze), (cx + 140, cy - 80 + squeeze)], fill=(255, 80, 80), width=10)
        d.line([(cx - 140, cy + 80 - squeeze), (cx + 140, cy + 80 - squeeze)], fill=(255, 80, 80), width=10)
        d.text((cx - 130, cy - 15), "COMPRESSIVE OBLIQUE MUSCLES", fill=(255, 100, 100), font=f_label)

        # Fluid conduits radiating out to leg joints
        for angle in [-140, -110, -70, -40, 40, 70, 110, 140]:
            rad = math.radians(angle)
            lx1 = cx + int(math.cos(rad) * 180)
            ly1 = cy + int(math.sin(rad) * 120)
            lx2 = cx + int(math.cos(rad) * 260)
            ly2 = cy + int(math.sin(rad) * 180)
            d.line([(lx1, ly1), (lx2, ly2)], fill=(0, 255, 200), width=8)

        # Pressure Gauge Display
        cur_kpa = 1.5 if squeeze < 0 else 52.0
        d.rectangle([cx - 180, cy + 190, cx + 180, cy + 260], fill=(10, 20, 35), outline=(0, 220, 255), width=2)
        d.text((cx - 160, cy + 205), f"HEMOLYMPH PRESSURE: {cur_kpa:.1f} kPa", fill=(0, 255, 180) if cur_kpa > 10 else (140, 180, 220), font=f_label)

        # Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "ARACHNID HYDRAULIC PRESSURE TELEMETRY", fill=(120, 180, 240), font=f_sub)
        bullets = [
            ("PRESSURE SPIKE", "50+ KILOPASCALS (SURGES FROM 1.5 kPa RESTING BASELINE)"),
            ("ANATOMICAL PARADOX", "LEGS CONTAIN ZERO EXTENSOR MUSCLES (CANNOT PUSH OPEN)"),
            ("HYDRAULIC TRANSMISSION", "HEMOLYMPH (BLOOD) PUMPED INSTANTLY INTO LEG JOINTS"),
            ("RESPONSE TIME", "PRESSURE APPLIED IN LESS THAN 10 MILLISECONDS"),
            ("PISTON EQUIVALENT", "ACTS LIKE HIGH-SPEED PNEUMATIC / HYDRAULIC ACTUATOR")
        ]
        for row_i, (k, v) in enumerate(bullets):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_spider_hydraulic_launch(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    f_title, f_sub, f_label, f_small = get_font(38, bold=True), get_font(24, mono=True), get_font(28, bold=True), get_font(20, mono=True)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        d = ImageDraw.Draw(img)
        for gx in range(0, VIDEO_WIDTH, 80): d.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80): d.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        d.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), 18, 2)
        d.text((80, 80), "HYDRAULIC LEG EXTENSION LAUNCH", fill=(255, 255, 255), font=f_title)
        d.text((80, 140), "50X BODY LENGTH LEAP POWERED BY FLUID EXPANSION", fill=(0, 210, 255), font=f_sub)

        # Center Diagram: Leg Joint Snapping Open
        box_mid = (50, 220, VIDEO_WIDTH - 50, 820)
        d.rectangle(box_mid, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(d, box_mid, (0, 220, 255), 24, 2)
        d.text((80, 240), "[FEMUR-TIBIA JOINT EXPANSION & TRAJECTORY VECTOR]", fill=(120, 180, 240), font=f_sub)

        # Leg joint extension simulation
        # Cycle: bent (flexed) -> sudden explosive snap straight (180 deg)
        cycle = (t * 1.5) % 2.0
        is_launch = cycle > 1.0
        joint_angle = 60 if not is_launch else 170

        # Femur segment
        jx1, jy1 = 300, 520
        d.line([(180, 620), (jx1, jy1)], fill=(100, 140, 180), width=16)
        d.text((160, 650), "FEMUR", fill=(140, 180, 220), font=f_small)

        # Tibia segment rotating on hinge
        rad = math.radians(joint_angle)
        jx2 = int(jx1 + math.cos(rad) * 220)
        jy2 = int(jy1 + math.sin(rad) * 220)
        d.line([(jx1, jy1), (jx2, jy2)], fill=(255, 210, 60), width=14)
        d.ellipse([jx1 - 18, jy1 - 18, jx1 + 18, jy1 + 18], fill=(0, 255, 200))
        d.text((jx1 - 40, jy1 - 35), "HINGE JOINT", fill=(0, 255, 200), font=f_small)

        # High pressure fluid wave shooting into joint
        if is_launch:
            d.line([(jx1, jy1), (jx2, jy2)], fill=(0, 255, 255), width=6)
            d.text((380, 380), "EXPLOSIVE HYDRAULIC EXTENSION!", fill=(0, 255, 140), font=f_label)
            # Launch Vector Arrow
            d.line([(580, 520), (740, 360)], fill=(255, 80, 80), width=8)
            d.polygon([(750, 350), (720, 360), (740, 380)], fill=(255, 80, 80))
            d.text((720, 320), "50x LEAP VECTOR", fill=(255, 100, 100), font=f_label)
        else:
            d.text((380, 380), "PRE-LOADED HYDRAULIC PRESSURE (FLEXED)", fill=(255, 220, 80), font=f_small)

        # Telemetry Box
        tbox = (50, 860, VIDEO_WIDTH - 50, 1380)
        d.rectangle(tbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(d, tbox, (0, 220, 255), 20, 2)
        d.text((80, 880), "JUMPING SPIDER KINEMATICS & BALLISTICS", fill=(120, 180, 240), font=f_sub)
        bullets = [
            ("LAUNCH DISTANCE", "UP TO 50x SPIDER'S BODY LENGTH (~25 CENTIMETERS)"),
            ("EXTENSION TIME", "LESS THAN 10 MILLISECONDS (FASTER THAN MUSCLE CONTRACTION)"),
            ("TAKEOFF SPEED", "1.8 METERS PER SECOND WITH ZERO RUN-UP ACCELERATION"),
            ("SAFETY DRAGLINE", "SPINS AN ANCHORED SILK LIFELINE IN MID-AIR ON EVERY JUMP"),
            ("APPLICATION", "INSPIRES MODERN SOFT ROBOTICS & MICRO-HYDRAULIC ACTUATORS")
        ]
        for row_i, (k, v) in enumerate(bullets):
            ry = 940 + row_i * 75
            d.text((80, ry), k, fill=(140, 160, 190), font=f_small)
            d.text((80, ry + 26), v, fill=(240, 245, 255), font=f_label)
            d.line([(80, ry + 60), (VIDEO_WIDTH - 80, ry + 60)], fill=(30, 50, 75), width=1)

        frames.append(img)
    save_and_transcode(frames, output_path)

def render_all_mechanisms():
    animations = [
        ("chameleon_iridophore_photonic_crystal_lattice.mp4", render_chameleon_iridophores, 6.0),
        ("chameleon_lattice_expansion_wavelength_shift.mp4", render_chameleon_lattice_shift, 7.0),
        ("hummingbird_wing_figure_eight_aerodynamic_trajectory.mp4", render_hummingbird_figure_eight, 6.0),
        ("leading_edge_vortex_dual_stroke_aerodynamic_lift.mp4", render_hummingbird_vortex_lift, 7.0),
        ("woodpecker_cranial_biomechanics_shock_absorption.mp4", render_woodpecker_cranial_shock, 6.0),
        ("woodpecker_hyoid_bone_hydraulic_seatbelt_skull.mp4", render_woodpecker_hyoid_seatbelt, 7.0),
        ("owl_wing_serrated_comb_micro_turbulence_acoustic.mp4", render_owl_serrated_comb, 6.0),
        ("owl_trailing_edge_acoustic_fringe_sound_cancellation.mp4", render_owl_trailing_fringe, 7.0),
        ("jellyfish_cnidocyte_osmotic_capsule_pressure_mechanism.mp4", render_jellyfish_cnidocyte_capsule, 6.0),
        ("nematocyst_harpoon_acceleration_five_million_g.mp4", render_nematocyst_harpoon_acceleration, 7.0),
        ("caterpillar_digestive_autolysis_cellular_broth_chrysalis.mp4", render_butterfly_autolysis, 6.0),
        ("imaginal_discs_stem_cell_organ_assembly_butterfly.mp4", render_butterfly_imaginal_discs, 7.0),
        ("jumping_spider_cephalothorax_hydraulic_pressure_pump.mp4", render_spider_hydraulic_pump, 6.0),
        ("hydraulic_leg_extension_hemolymph_pressure_launch.mp4", render_spider_hydraulic_launch, 7.0)
    ]

    print(f"🚀 Rendering all {len(animations)} dedicated procedural mechanism animations...")
    t0 = time.time()
    for i, (fname, func, dur) in enumerate(animations):
        dest = ASSETS_VIDEOS / fname
        if not dest.exists():
            print(f"[{i+1}/{len(animations)}] Rendering '{fname}' ({dur}s)...")
            func(dest, duration=dur)
            print(f"   -> Saved: {dest} ({dest.stat().st_size / 1024:.1f} KB)")
        else:
            print(f"[{i+1}/{len(animations)}] Exists: {fname}")
    elapsed = time.time() - t0
    print(f"🎉 Done! All 14 mechanism animations rendered in {elapsed:.1f}s.")

if __name__ == "__main__":
    render_all_mechanisms()
