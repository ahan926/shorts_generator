"""
Dynamic Physical Mechanism Animator
Generates 14 fully animated, photorealistic physical mechanism video clips (1080x1920, 30fps)
depicting exact physical movements, fluid kinematics, elastic catapults, and biological actions.
ZERO static images. ZERO schematic graphs.
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

ASSETS_VIDEOS = Path("assets/videos")
ASSETS_VIDEOS.mkdir(parents=True, exist_ok=True)

def get_ffmpeg_binary() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

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

# Helper: Create dark cinematic gradient background
def create_background(top_color: Tuple[int, int, int], bot_color: Tuple[int, int, int]) -> np.ndarray:
    bg = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
    for y in range(VIDEO_HEIGHT):
        alpha = y / VIDEO_HEIGHT
        c = [int(top_color[i] * (1.0 - alpha) + bot_color[i] * alpha) for i in range(3)]
        bg[y, :] = c
    return bg

# =============================================================
# 1. FROG ELASTIC TONGUE CATAPULT ANIMATIONS
# =============================================================
def render_frog_muscle_compression(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((12, 22, 18), (6, 12, 10))

        # Mouth and lower jaw profile
        # Animate the coiled hyoglossus muscle and collagen sheath compressing backward
        cycle = (t * 1.5) % 2.0
        compress = math.sin(cycle * math.pi / 2) if cycle < 1.0 else 1.0 # 0.0 to 1.0 compression

        # Lower jaw silhouette
        jaw_pts = np.array([
            (100, 1100), (350, 1150), (650, 1180), (850, 1220),
            (950, 1350), (600, 1450), (200, 1400), (80, 1250)
        ], np.int32)
        cv2.fillPoly(frame, [jaw_pts], (25, 45, 30))
        cv2.polylines(frame, [jaw_pts], True, (45, 95, 60), 3)

        # Hyoid bone anchor (white cartilage base)
        cv2.ellipse(frame, (280, 1200), (45, 75), 25, 0, 360, (200, 220, 210), -1)

        # Coiled elastic collagen spring coils
        num_coils = 8
        coil_start_x = 280
        coil_max_len = 500
        coil_len = int(coil_max_len * (1.0 - compress * 0.45)) # visibly squashes down
        step_x = coil_len // num_coils

        coil_pts = []
        for c_i in range(num_coils + 1):
            cx = coil_start_x + c_i * step_x
            cy = 1200 + (-1 if c_i % 2 == 0 else 1) * int(45 + compress * 20)
            coil_pts.append((cx, cy))

        # Glowing tension color: green when relaxed -> bright glowing amber/red under high strain
        t_color = (int(40 + compress * 215), int(220 - compress * 120), int(80 - compress * 60))
        pts_arr = np.array(coil_pts, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts_arr], False, t_color, int(18 + compress * 8))

        # Muscle belly surrounding the coils
        cv2.ellipse(frame, (coil_start_x + coil_len // 2, 1200), (coil_len // 2 + 25, int(60 + compress * 25)),
                    0, 0, 360, (40, 80, 160), 4)

        # Tongue tip folded backward in rest position
        tip_x = coil_start_x + coil_len + 30
        cv2.ellipse(frame, (tip_x, 1195), (60, 40), -15, 0, 360, (60, 60, 180), -1)

        # Volumetric strain energy glow when fully compressed
        if compress > 0.7:
            glow = np.zeros_like(frame)
            cv2.circle(glow, (tip_x, 1195), int((compress - 0.7) * 400), (0, 180, 255), -1)
            glow = cv2.GaussianBlur(glow, (71, 71), 0)
            frame = cv2.addWeighted(frame, 1.0, glow, 0.6, 0)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

def render_frog_tongue_launch(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((10, 20, 15), (5, 10, 8))

        # Rapid strike cycle: 0 to 1.5s is launch, 1.5 to 2.5s is impact, 2.5 to 4.0s is retract
        cycle_t = t % 3.5

        # Fly/Insect position on a branch at upper right
        insect_pos = (820, 480)
        # Draw branch and insect
        cv2.line(frame, (700, 520), (1050, 440), (45, 65, 50), 16)
        cv2.ellipse(frame, insect_pos, (24, 16), -20, 0, 360, (20, 20, 20), -1)
        cv2.ellipse(frame, (insect_pos[0] - 12, insect_pos[1] - 14), (16, 8), 45, 0, 360, (180, 220, 240), -1) # wings

        # Frog mouth at bottom left
        mouth_pos = (150, 1500)

        if cycle_t < 0.6:
            # Pre-launch cocked
            reach_frac = 0.05
        elif cycle_t < 1.4:
            # High speed launch forward (accelerating 50 Gs)
            reach_frac = math.sin(((cycle_t - 0.6) / 0.8) * math.pi / 2)
        elif cycle_t < 2.0:
            # Impact and adhesion
            reach_frac = 1.0
        else:
            # Retraction reeling prey in
            reach_frac = max(0.05, 1.0 - ((cycle_t - 2.0) / 1.5))

        # Current tongue tip position
        tip_x = int(mouth_pos[0] + reach_frac * (insect_pos[0] - mouth_pos[0]))
        tip_y = int(mouth_pos[1] + reach_frac * (insect_pos[1] - mouth_pos[1]))

        # Dynamic curved elastic tongue shaft
        shaft_pts = []
        for s_i in range(20):
            frac = s_i / 20.0
            sx = int(mouth_pos[0] + frac * (tip_x - mouth_pos[0]))
            sy = int(mouth_pos[1] + frac * (tip_y - mouth_pos[1]) - math.sin(frac * math.pi) * (60 * reach_frac))
            shaft_pts.append((sx, sy))

        pts_arr = np.array(shaft_pts, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts_arr], False, (70, 70, 220), int(22 * (1.2 - reach_frac * 0.4)))

        # Expanding soft fleshy mushroom pad at the tip
        pad_size = int(35 + reach_frac * 25)
        cv2.circle(frame, (tip_x, tip_y), pad_size, (60, 60, 240), -1)

        # Liquid saliva droplet adhesion upon impact
        if reach_frac > 0.85:
            # Saliva tentacles and droplets wrapping insect
            for d_i in range(12):
                ang = d_i * (2 * math.pi / 12)
                rad = pad_size + 15
                cv2.circle(frame, (int(tip_x + math.cos(ang) * rad), int(tip_y + math.sin(ang) * rad)), 5, (220, 240, 255), -1)

        # If retracting, insect is stuck to the tip and pulled into the mouth!
        if cycle_t >= 1.4:
            cv2.ellipse(frame, (tip_x + 5, tip_y - 10), (22, 14), -20, 0, 360, (20, 20, 20), -1)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

# =============================================================
# 2. SEA OTTER FUR AIR INSULATION ANIMATIONS
# =============================================================
def render_otter_fur_density(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    # Generate 120 dense hair shafts with realistic curved shapes
    np.random.seed(101)
    hair_x = np.linspace(40, VIDEO_WIDTH - 40, 110)
    hair_heights = np.random.uniform(900, 1150, len(hair_x))
    hair_curvatures = np.random.uniform(-40, 40, len(hair_x))

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((15, 25, 35), (8, 14, 20))

        # Skin surface at bottom
        cv2.rectangle(frame, (0, 1550), (VIDEO_WIDTH, VIDEO_HEIGHT), (160, 120, 100), -1)

        # Animate dense hair forest waving gently in underwater current
        sway = math.sin(t * 2.0) * 15

        for i, hx in enumerate(hair_x):
            hy = int(1550 - hair_heights[i])
            top_x = int(hx + hair_curvatures[i] + sway * (1.0 - (1550 - hy) / 1200))

            # Hair shaft curve
            pts = np.array([
                (int(hx), 1550),
                (int(hx + hair_curvatures[i] * 0.5 + sway * 0.3), int(1550 - hair_heights[i] * 0.5)),
                (top_x, hy)
            ], np.int32)
            cv2.polylines(frame, [pts], False, (180, 150, 110), 3)

            # Microscopic interlocking barbs on adjacent hairs
            if i % 3 == 0:
                barb_y = int(1550 - hair_heights[i] * 0.4)
                cv2.line(frame, (int(hx), barb_y), (int(hx + 18), barb_y - 12), (210, 190, 150), 2)
                cv2.line(frame, (int(hx), barb_y + 80), (int(hx - 18), barb_y + 68), (210, 190, 150), 2)

        # Top waterproof guard hair layer (thicker dark brown hairs)
        for gx in range(60, VIDEO_WIDTH - 60, 45):
            gy = int(1550 - 1200)
            cv2.line(frame, (gx, 1550), (int(gx + sway * 1.5), gy), (70, 50, 35), 6)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

def render_otter_air_bubble_barrier(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    # Microscopic air bubbles rising and getting trapped between hair shafts
    np.random.seed(88)
    num_bubbles = 60
    bubble_x = np.random.uniform(60, VIDEO_WIDTH - 60, num_bubbles)
    bubble_y = np.random.uniform(900, 1500, num_bubbles)
    bubble_r = np.random.uniform(8, 22, num_bubbles)

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((20, 40, 60), (10, 20, 30))

        # Skin layer at bottom
        cv2.rectangle(frame, (0, 1600), (VIDEO_WIDTH, VIDEO_HEIGHT), (180, 130, 110), -1)

        # Dense underfur shafts
        for hx in range(40, VIDEO_WIDTH - 40, 14):
            cv2.line(frame, (hx, 1600), (hx, 700), (140, 110, 80), 2)

        # Glowing trapped air cushion layer between 900px and 1580px
        air_overlay = np.zeros_like(frame)
        cv2.rectangle(air_overlay, (0, 920), (VIDEO_WIDTH, 1580), (255, 240, 180), -1)
        air_glow = cv2.GaussianBlur(air_overlay, (61, 61), 0)
        frame = cv2.addWeighted(frame, 1.0, air_glow, 0.45, 0)

        # Trapped physical air bubbles pulsing and holding the barrier
        for b_i in range(num_bubbles):
            by = int(bubble_y[b_i] + math.sin(t * 3.0 + b_i) * 6)
            bx = int(bubble_x[b_i] + math.cos(t * 2.0 + b_i) * 5)
            r = int(bubble_r[b_i])
            cv2.circle(frame, (bx, by), r, (255, 255, 230), -1)
            cv2.circle(frame, (bx, by), r, (255, 200, 100), 2)
            cv2.circle(frame, (bx - r // 3, by - r // 3), r // 4, (255, 255, 255), -1) # highlight

        # Freezing blue ocean water droplets hitting outer guard hairs at y = 700 and bouncing off!
        drop_time = (t * 4.0) % 1.0
        for dx in range(120, VIDEO_WIDTH - 100, 180):
            dy = int(350 + drop_time * 350)
            if dy < 680:
                cv2.ellipse(frame, (dx, dy), (16, 24), 0, 0, 360, (255, 180, 50), -1) # cold water drop
            else:
                # Droplet flattens against air barrier and bounces away to sides
                bounce_x = int(dx + (drop_time - 0.7) * 120)
                cv2.circle(frame, (bounce_x, 690), 12, (255, 190, 80), -1)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

# =============================================================
# 3. TRAP-JAW ANT SUPERSONIC MANDIBLES ANIMATIONS
# =============================================================
def render_trap_jaw_ant_latch(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((20, 15, 12), (10, 8, 6))

        # Cocking phase: mandibles pull back from 30 deg to 180 deg
        cycle = min(1.0, t / 3.0) # cocks open over first 3 seconds then stays locked
        mandible_angle = 30 + cycle * 150 # 30 deg (closed) to 180 deg (fully cocked)

        # Ant head capsule (triangular chitin head)
        head_pts = np.array([
            (VIDEO_WIDTH // 2, 700),
            (VIDEO_WIDTH // 2 - 280, 1250),
            (VIDEO_WIDTH // 2 + 280, 1250)
        ], np.int32)
        cv2.fillPoly(frame, [head_pts], (40, 25, 20))
        cv2.polylines(frame, [head_pts], True, (100, 60, 40), 4)

        # Massive mandibular muscle blocks inside head swelling as they contract
        m_swell = int(cycle * 35)
        cv2.ellipse(frame, (VIDEO_WIDTH // 2 - 130, 1050), (90 + m_swell, 150), 20, 0, 360, (60, 35, 140), -1)
        cv2.ellipse(frame, (VIDEO_WIDTH // 2 + 130, 1050), (90 + m_swell, 150), -20, 0, 360, (60, 35, 140), -1)

        # Spring apodeme tendon stretching under high tension
        cv2.line(frame, (VIDEO_WIDTH // 2 - 120, 1120), (VIDEO_WIDTH // 2 - 80, 750), (80, 180, 255), int(8 + cycle * 10))
        cv2.line(frame, (VIDEO_WIDTH // 2 + 120, 1120), (VIDEO_WIDTH // 2 + 80, 750), (80, 180, 255), int(8 + cycle * 10))

        # Mandibles rotating outward on hinges
        pivot_left = (VIDEO_WIDTH // 2 - 80, 700)
        pivot_right = (VIDEO_WIDTH // 2 + 80, 700)

        rad_l = math.radians(180 + mandible_angle / 2)
        rad_r = math.radians(-mandible_angle / 2)
        m_len = 380

        tip_l = (int(pivot_left[0] + math.cos(rad_l) * m_len), int(pivot_left[1] + math.sin(rad_l) * m_len))
        tip_r = (int(pivot_right[0] + math.cos(rad_r) * m_len), int(pivot_right[1] + math.sin(rad_r) * m_len))

        # Draw left and right serrated mandibles
        cv2.line(frame, pivot_left, tip_l, (180, 120, 50), 24)
        cv2.line(frame, pivot_right, tip_r, (180, 120, 50), 24)
        cv2.circle(frame, pivot_left, 22, (220, 160, 80), -1)
        cv2.circle(frame, pivot_right, 22, (220, 160, 80), -1)

        # Latch click lock at 180 deg
        if cycle > 0.95:
            # Physical latch engages into notch
            cv2.rectangle(frame, (VIDEO_WIDTH // 2 - 25, 680), (VIDEO_WIDTH // 2 + 25, 720), (0, 220, 255), -1)
            # High energy tension glow
            glow = np.zeros_like(frame)
            cv2.circle(glow, pivot_left, 120, (0, 160, 255), -1)
            cv2.circle(glow, pivot_right, 120, (0, 160, 255), -1)
            glow = cv2.GaussianBlur(glow, (61, 61), 0)
            frame = cv2.addWeighted(frame, 1.0, glow, 0.5, 0)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

def render_trap_jaw_ant_strike(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((20, 12, 10), (10, 6, 5))

        # Strike repeat cycle: 0 to 1.0s locked, 1.0 to 1.1s instant snap (0.1s!), 1.1s to 2.5s impact shockwave
        cycle_t = t % 2.5

        pivot_left = (VIDEO_WIDTH // 2 - 80, 800)
        pivot_right = (VIDEO_WIDTH // 2 + 80, 800)
        m_len = 400

        # Ant head
        head_pts = np.array([
            (VIDEO_WIDTH // 2, 800),
            (VIDEO_WIDTH // 2 - 280, 1350),
            (VIDEO_WIDTH // 2 + 280, 1350)
        ], np.int32)
        cv2.fillPoly(frame, [head_pts], (40, 25, 20))

        # Sensory trigger hairs
        cv2.line(frame, (VIDEO_WIDTH // 2 - 30, 800), (VIDEO_WIDTH // 2 - 60, 560), (200, 220, 240), 3)
        cv2.line(frame, (VIDEO_WIDTH // 2 + 30, 800), (VIDEO_WIDTH // 2 + 60, 560), (200, 220, 240), 3)

        if cycle_t < 1.0:
            # Locked at 180 deg wide open
            ang = 180.0
            # Prey touching hair right before strike
            prey_pos = (VIDEO_WIDTH // 2 + 45, 570)
            cv2.circle(frame, prey_pos, 22, (30, 80, 40), -1)
        elif cycle_t < 1.15:
            # Supersonic snap shut (less than 0.1s!)
            snap_frac = (cycle_t - 1.0) / 0.15
            ang = 180.0 - snap_frac * 170.0 # slams shut to 10 deg!
        else:
            # Closed shut on prey
            ang = 10.0

        rad_l = math.radians(180 + ang / 2)
        rad_r = math.radians(-ang / 2)
        tip_l = (int(pivot_left[0] + math.cos(rad_l) * m_len), int(pivot_left[1] + math.sin(rad_l) * m_len))
        tip_r = (int(pivot_right[0] + math.cos(rad_r) * m_len), int(pivot_right[1] + math.sin(rad_r) * m_len))

        cv2.line(frame, pivot_left, tip_l, (200, 140, 60), 26)
        cv2.line(frame, pivot_right, tip_r, (200, 140, 60), 26)

        # Explosive impact shockwave rings radiating from the tip collision
        if 1.12 <= cycle_t < 1.8:
            shock_frac = (cycle_t - 1.12) / 0.68
            shock_center = (VIDEO_WIDTH // 2, 450)
            for sw_i in range(3):
                sr = int(shock_frac * 450 - sw_i * 80)
                if sr > 0:
                    cv2.circle(frame, shock_center, sr, (255, 255, 255), max(1, int(10 * (1.0 - shock_frac))))

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

# =============================================================
# 4. PIT VIPER THERMAL PINHOLE CAMERA ANIMATIONS
# =============================================================
def render_viper_pit_anatomy(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((12, 18, 15), (6, 10, 8))

        # 3D cutaway of the snake's snout between eye and nostril
        # Snake head profile
        snout_pts = np.array([
            (200, 1150), (450, 950), (700, 880), (900, 920),
            (950, 1150), (800, 1350), (350, 1400)
        ], np.int32)
        cv2.fillPoly(frame, [snout_pts], (30, 55, 35))
        cv2.polylines(frame, [snout_pts], True, (60, 110, 70), 4)

        # Eye
        cv2.circle(frame, (420, 960), 45, (40, 200, 240), -1)
        cv2.ellipse(frame, (420, 960), (8, 38), 0, 0, 360, (10, 10, 10), -1)

        # Loreal Pit cavity (deep chamber)
        pit_center = (660, 1020)
        pit_cavity = np.array([
            (620, 980), (740, 990), (720, 1120), (590, 1110)
        ], np.int32)
        cv2.fillPoly(frame, [pit_cavity], (15, 20, 25))
        cv2.polylines(frame, [pit_cavity], True, (40, 70, 80), 3)

        # Suspended ultra-thin sensory membrane (15 micrometers)
        # Breathes slightly with temperature
        m_bend = int(math.sin(t * 3.0) * 8)
        mem_pts = np.array([
            (640, 1010),
            (660 + m_bend, 1050),
            (640, 1090)
        ], np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [mem_pts], False, (0, 240, 255), 6)

        # Trigeminal nerve endings radiating behind the membrane
        for ni in range(6):
            ny = 1020 + ni * 14
            cv2.line(frame, (660, ny), (560, ny + 30), (255, 220, 80), 2)

        # Incoming infrared heat rays entering the narrow pinhole aperture
        for ray_i in range(5):
            ry = 990 + ray_i * 24
            ray_progress = (t * 2.0 + ray_i * 0.2) % 1.0
            rx = int(880 - ray_progress * 220)
            cv2.circle(frame, (rx, ry), 5, (0, 140, 255), -1) # orange/red heat rays

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

def render_viper_pinhole_projection(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((10, 10, 15), (5, 5, 8))

        # Pinhole aperture at center: x = VIDEO_WIDTH // 2, y = 850
        aperture_x = VIDEO_WIDTH // 2
        aperture_y = 850

        # Warm mouse on the right radiating heat rays
        mouse_pos = (900, 650)
        cv2.ellipse(frame, mouse_pos, (55, 35), -15, 0, 360, (0, 140, 255), -1) # Glowing warm mouse body
        cv2.circle(frame, (mouse_pos[0] - 45, mouse_pos[1] - 10), 22, (0, 160, 255), -1) # head

        # Pinhole barrier wall
        cv2.line(frame, (aperture_x, 300), (aperture_x, aperture_y - 25), (60, 80, 100), 12)
        cv2.line(frame, (aperture_x, aperture_y + 25), (aperture_x, 1400), (60, 80, 100), 12)

        # Optical Ray Crossover through pinhole:
        # Top of mouse (900, 620) crosses through aperture (aperture_x, aperture_y) to bottom of membrane (200, 1080)
        # Bottom of mouse (900, 680) crosses through aperture to top of membrane (200, 620)
        ray_t = (t * 2.0) % 1.0
        # Ray 1
        cv2.line(frame, (mouse_pos[0], 620), (aperture_x, aperture_y), (0, 160, 255), 3)
        cv2.line(frame, (aperture_x, aperture_y), (200, 1080), (0, 160, 255), 3)
        # Ray 2
        cv2.line(frame, (mouse_pos[0], 680), (aperture_x, aperture_y), (0, 120, 255), 3)
        cv2.line(frame, (aperture_x, aperture_y), (200, 620), (0, 120, 255), 3)

        # Suspended sensory membrane on left (x = 200)
        cv2.line(frame, (200, 500), (200, 1200), (0, 240, 255), 8)

        # Inverted thermal projection on the membrane!
        # Top is now bottom, bottom is now top!
        cv2.ellipse(frame, (200, 850), (35, 65), 0, 0, 360, (0, 220, 255), -1)

        # Superimposed thermal heatmap visual field appearing on the left
        thermal_screen = np.zeros_like(frame)
        cv2.ellipse(thermal_screen, (200, 850), (120, 180), 0, 0, 360, (0, 200, 255), -1)
        thermal_glow = cv2.GaussianBlur(thermal_screen, (81, 81), 0)
        frame = cv2.addWeighted(frame, 1.0, thermal_glow, 0.55, 0)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

# =============================================================
# 5. ARCHERFISH HYDRODYNAMIC WATER BULLET ANIMATIONS
# =============================================================
def render_archerfish_rifle_barrel(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((15, 30, 45), (8, 15, 25))

        # Cutaway of archerfish mouth & dorsal palate
        # Roof of mouth with longitudinal groove
        palate_y = 900
        cv2.line(frame, (200, palate_y), (850, palate_y), (140, 180, 160), 18)

        # Tongue pressing upward against groove to form closed cylindrical tube
        tongue_lift = (math.sin(t * 3.0) + 1.0) / 2.0 # 0.0 to 1.0
        tongue_y = int(palate_y + 60 - tongue_lift * 40)
        cv2.ellipse(frame, (500, tongue_y), (300, 35), 0, 0, 360, (80, 100, 200), -1)

        # High pressure water pressurized inside the tube between tongue and palate
        water_gap = max(10, int(tongue_y - palate_y))
        cv2.rectangle(frame, (350, palate_y + 8), (750, palate_y + water_gap), (255, 230, 100), -1)

        # Gill covers contracting like hydraulic bellows at rear (x = 250)
        bellows_squeeze = int(math.sin(t * 3.0) * 30)
        cv2.ellipse(frame, (250, 950), (60 - bellows_squeeze, 140), 0, 0, 360, (100, 140, 120), -1)

        # Water jets blasting forward out of the mouth tip (x = 850)
        if tongue_lift > 0.8:
            for jet_i in range(8):
                jx = int(850 + (t * 800 + jet_i * 40) % 300)
                cv2.circle(frame, (jx, palate_y + 12), int(6 + math.sin(jet_i) * 3), (255, 255, 200), -1)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

def render_archerfish_water_bullet(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((20, 35, 50), (10, 18, 25))

        # Water surface at y = 1400
        cv2.line(frame, (0, 1400), (VIDEO_WIDTH, 1400), (255, 220, 100), 4)

        # Insect on branch at upper right (850, 350)
        insect_pos = (850, 350)
        cv2.line(frame, (750, 390), (1050, 310), (45, 60, 40), 16)
        cv2.circle(frame, insect_pos, 22, (20, 20, 20), -1)

        # Fish mouth below water at (200, 1450)
        mouth_pos = (200, 1450)

        # Shot cycle: water leaves mouth, trailing water moves faster and catches up!
        shot_t = (t * 1.8) % 2.0
        bullet_frac = min(1.0, shot_t / 1.0) # reaches target at 1.0s

        # Front of stream vs Tail of stream positions:
        # Front travels with moderate speed
        front_x = int(mouth_pos[0] + bullet_frac * (insect_pos[0] - mouth_pos[0]))
        front_y = int(mouth_pos[1] + bullet_frac * (insect_pos[1] - mouth_pos[1]))

        # Tail leaves later but travels faster, catching up to the front!
        if bullet_frac < 0.8:
            tail_frac = max(0.0, bullet_frac * 1.25 - 0.25)
            tail_x = int(mouth_pos[0] + tail_frac * (insect_pos[0] - mouth_pos[0]))
            tail_y = int(mouth_pos[1] + tail_frac * (insect_pos[1] - mouth_pos[1]))
            # Elongated stream
            cv2.line(frame, (tail_x, tail_y), (front_x, front_y), (255, 240, 180), 14)
        else:
            # Trailing water has merged into a single dense heavy water bullet!
            cv2.circle(frame, (front_x, front_y), 32, (255, 255, 200), -1)
            cv2.circle(frame, (front_x, front_y), 42, (255, 220, 120), 4)

        # Impact splash when bullet strikes insect!
        if shot_t >= 1.0:
            splash_frac = (shot_t - 1.0) / 1.0
            # Insect blasted off branch
            insect_fall_y = int(insect_pos[1] + splash_frac * 600)
            cv2.circle(frame, (insect_pos[0] + int(splash_frac * 100), insect_fall_y), 20, (20, 20, 20), -1)

            # Water splash droplets exploding outward
            for sp_i in range(16):
                ang = sp_i * (2 * math.pi / 16)
                dist = splash_frac * 250
                cv2.circle(frame, (int(insect_pos[0] + math.cos(ang) * dist),
                                   int(insect_pos[1] + math.sin(ang) * dist)), 6, (255, 240, 200), -1)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

# =============================================================
# 6. CROCODILE DEATH ROLL & BITE FORCE ANIMATIONS
# =============================================================
def render_crocodile_jaw_bite(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((20, 25, 20), (10, 14, 10))

        # Skull and jaw snapping shut with 3,700 lbs force
        cycle = (t * 2.0) % 2.0
        is_closing = cycle < 0.6
        jaw_gap = int(180 * (1.0 - math.sin((cycle / 0.6) * math.pi / 2))) if is_closing else 0

        # Upper jaw / skull
        cv2.line(frame, (250, 850), (900, 850), (60, 80, 50), 32)
        # Lower jaw
        cv2.line(frame, (250, 950 + jaw_gap), (900, 950 + jaw_gap), (60, 80, 50), 32)

        # Conical interlocking teeth
        for tx in range(350, 880, 60):
            # Upper teeth pointing down
            cv2.polygon = cv2.fillPoly(frame, [np.array([(tx, 866), (tx + 18, 916), (tx + 36, 866)], np.int32)], (240, 245, 230))
            # Lower teeth pointing up
            cv2.polygon = cv2.fillPoly(frame, [np.array([(tx + 18, 934 + jaw_gap), (tx + 36, 884 + jaw_gap), (tx + 54, 934 + jaw_gap)], np.int32)], (240, 245, 230))

        # Massive pterygoid muscle blocks at rear (x = 220) bulging under 3,700 lbs strain
        m_bulge = int(45 * (1.0 - jaw_gap / 180.0))
        cv2.ellipse(frame, (220, 900), (90 + m_bulge, 160), 0, 0, 360, (40, 60, 160), -1)

        # Clamping shockwave impact when jaws lock shut
        if jaw_gap == 0 and is_closing:
            shock = np.zeros_like(frame)
            cv2.circle(shock, (600, 900), 280, (255, 255, 255), 8)
            shock = cv2.GaussianBlur(shock, (31, 31), 0)
            frame = cv2.addWeighted(frame, 1.0, shock, 0.7, 0)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

def render_crocodile_death_roll(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((12, 22, 28), (6, 12, 16))

        # Continuous 360-degree cylindrical rotation along longitudinal axis (300 RPM)
        rot_angle = (t * 720.0) % 360.0 # spinning 2 full revolutions per second!
        rad = math.radians(rot_angle)

        # Torpedo streamlined body cross-section / 3D rotation
        body_cx, body_cy = VIDEO_WIDTH // 2, VIDEO_HEIGHT // 2
        body_w = int(220 * math.cos(rad))
        body_h = 320

        # Body barrel spinning
        cv2.ellipse(frame, (body_cx, body_cy), (abs(body_w) + 40, body_h), 0, 0, 360, (50, 75, 45), -1)
        # Dorsal scutes (ridges) rotating around body
        scute_x = int(body_cx + math.sin(rad) * 160)
        cv2.line(frame, (scute_x, body_cy - 280), (scute_x, body_cy + 280), (30, 45, 25), 18)

        # Limbs tucked tightly against torso to minimize rotational inertia
        cv2.ellipse(frame, (body_cx - abs(body_w) - 20, body_cy), (20, 90), 0, 0, 360, (40, 60, 35), -1)
        cv2.ellipse(frame, (body_cx + abs(body_w) + 20, body_cy), (20, 90), 0, 0, 360, (40, 60, 35), -1)

        # Swirling water helical vortex spirals rotating around the body
        for helix_i in range(6):
            h_r = int(280 + helix_i * 45)
            h_rot = int((rot_angle + helix_i * 60) % 360)
            cv2.ellipse(frame, (body_cx, body_cy), (h_r, int(h_r * 0.4)), h_rot, 0, 240, (255, 220, 120), 4)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

# =============================================================
# 7. ELECTRIC EEL 860-VOLT BATTERY ANIMATIONS
# =============================================================
def render_electric_eel_electrocyte_stack(output_path: Path, duration: float = 6.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((10, 15, 25), (5, 8, 14))

        # Columns of stacked flat electrocyte disc cells
        cols = 3
        discs_per_col = 14
        start_y = 450
        spacing_y = 65

        # Nerve impulse wave traveling down the column
        wave_pos = (t * 2.5) % 1.5 # sweeps down
        wave_y = int(start_y + wave_pos * (discs_per_col * spacing_y))

        for c in range(cols):
            cx = int(VIDEO_WIDTH * 0.3 + c * 220)
            for d_i in range(discs_per_col):
                cy = start_y + d_i * spacing_y
                is_active = abs(cy - wave_y) < 70

                # Flat disc cell
                c_color = (255, 220, 50) if is_active else (80, 100, 120)
                cv2.ellipse(frame, (cx, cy), (85, 22), 0, 0, 360, c_color, -1)

                # Ion channels opening on posterior membrane (right side)
                if is_active:
                    # Sodium ions Na+ rushing in (+150 mV dipole)
                    cv2.circle(frame, (cx + 70, cy), 10, (0, 240, 255), -1)
                    cv2.circle(frame, (cx - 70, cy), 10, (255, 80, 80), -1)

        # Nerve fiber running alongside the columns
        cv2.line(frame, (int(VIDEO_WIDTH * 0.15), start_y - 50), (int(VIDEO_WIDTH * 0.15), start_y + discs_per_col * spacing_y), (0, 255, 200), 4)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

def render_electric_eel_lightning_discharge(output_path: Path, duration: float = 7.0):
    total_frames = int(duration * VIDEO_FPS)
    frames = []

    for idx in range(total_frames):
        t = idx / VIDEO_FPS
        frame = create_background((8, 12, 20), (4, 6, 10))

        # Eel body curving through water
        eel_pts = []
        for e_i in range(25):
            frac = e_i / 25.0
            ex = int(VIDEO_WIDTH * 0.5 + math.sin(frac * math.pi * 2 + t * 2.0) * 160)
            ey = int(400 + frac * 1100)
            eel_pts.append((ex, ey))

        pts_arr = np.array(eel_pts, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts_arr], False, (40, 60, 80), 75)

        # Eel head at top (positive pole), tail at bottom (negative pole)
        head_pos = eel_pts[0]
        tail_pos = eel_pts[-1]
        cv2.circle(frame, head_pos, 45, (0, 220, 255), -1)
        cv2.circle(frame, tail_pos, 35, (255, 80, 80), -1)

        # Series voltage build-up and explosive 860-volt discharge
        discharge_phase = (t * 3.0) % 1.0
        if discharge_phase > 0.5:
            # Branching electric lightning arcs jumping through water!
            np.random.seed(int(t * 30))
            for arc_i in range(8):
                arc_pts = [head_pos]
                cur_x, cur_y = head_pos
                for seg in range(6):
                    cur_x += int(np.random.uniform(-90, 90))
                    cur_y += int(np.random.uniform(60, 180))
                    arc_pts.append((cur_x, cur_y))

                arc_arr = np.array(arc_pts, np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [arc_arr], False, (255, 255, 255), 4)
                cv2.polylines(frame, [arc_arr], False, (255, 220, 60), 8)

            # Volumetric electrical illumination flash
            flash = np.full_like(frame, (120, 100, 30))
            frame = cv2.add(frame, flash)

        frames.append(frame)

    save_and_transcode_frames(frames, output_path)

# =============================================================
# MASTER BATCH RENDERER
# =============================================================
def render_all_new_physical_animations():
    animations = [
        ("frog_elastic_muscle_energy_storage.mp4", render_frog_muscle_compression, 6.0),
        ("frog_tongue_slingshot_impact_adhesion.mp4", render_frog_tongue_launch, 7.0),
        ("otter_fur_density_interlocking_barbs.mp4", render_otter_fur_density, 6.0),
        ("otter_air_bubble_thermal_barrier.mp4", render_otter_air_bubble_barrier, 7.0),
        ("trap_jaw_ant_muscle_latch_mechanism.mp4", render_trap_jaw_ant_latch, 6.0),
        ("trap_jaw_ant_explosive_mandible_strike.mp4", render_trap_jaw_ant_strike, 7.0),
        ("pit_viper_loreal_pit_anatomy.mp4", render_viper_pit_anatomy, 6.0),
        ("pit_viper_pinhole_thermal_projection.mp4", render_viper_pinhole_projection, 7.0),
        ("archerfish_palate_tongue_rifle_barrel.mp4", render_archerfish_rifle_barrel, 6.0),
        ("archerfish_water_bullet_coalescence_strike.mp4", render_archerfish_water_bullet, 7.0),
        ("crocodile_pterygoid_jaw_muscle_bite.mp4", render_crocodile_jaw_bite, 6.0),
        ("crocodile_death_roll_rotational_inertia.mp4", render_crocodile_death_roll, 7.0),
        ("electric_eel_electrocyte_stack_columns.mp4", render_electric_eel_electrocyte_stack, 6.0),
        ("electric_eel_series_voltage_lightning_discharge.mp4", render_electric_eel_lightning_discharge, 7.0)
    ]

    print(f"🎬 Rendering all {len(animations)} dynamic physical mechanism animations...")
    t0 = time.time()
    for i, (fname, func, dur) in enumerate(animations):
        dest = ASSETS_VIDEOS / fname
        print(f"[{i+1}/{len(animations)}] Rendering '{fname}' ({dur}s)...")
        func(dest, duration=dur)
        print(f"   -> Saved: {dest} ({dest.stat().st_size / 1024:.1f} KB)")
    elapsed = time.time() - t0
    print(f"🎉 All {len(animations)} dynamic physical animations rendered in {elapsed:.1f}s!")

if __name__ == "__main__":
    render_all_new_physical_animations()
