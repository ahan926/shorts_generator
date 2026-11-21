"""
Master Realistic Cartoon Animator
Generates 14 full multi-stage animated cartoon sequences (1080x1920 @ 30fps)
featuring high-end cel-shaded biological illustrations, articulated movement,
dynamic fluid/particle physics, supersonic shockwaves, and anatomical HUD callouts.
"""

import math
import os
import subprocess
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH = 1080
HEIGHT = 1920
FPS = 30
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==============================================================================
# Easing & Math Helpers
# ==============================================================================
def clamp(val, min_val=0.0, max_val=1.0):
    return max(min_val, min(max_val, float(val)))

def ease_in_out(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)

def ease_out_quad(t):
    t = clamp(t)
    return 1.0 - (1.0 - t) * (1.0 - t)

def ease_in_quad(t):
    t = clamp(t)
    return t * t

def ease_out_elastic(t):
    t = clamp(t)
    if t == 0: return 0.0
    if t == 1: return 1.0
    p = 0.3
    return math.pow(2, -10 * t) * math.sin((t - p / 4) * (2 * math.pi) / p) + 1.0

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_pt(p1, p2, t):
    return (int(lerp(p1[0], p2[0], t)), int(lerp(p1[1], p2[1], t)))


# ==============================================================================
# Drawing Utilities (Cel Shading, HUD Badges, Springs, Sparks)
# ==============================================================================
def get_font(size=36, bold=True):
    try:
        font_path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def draw_hud_badge(draw, x, y, title, subtitle="", color=(255, 215, 0), bg=(15, 22, 32, 235)):
    font_title = get_font(34, bold=True)
    font_sub = get_font(26, bold=False)
    
    pad_x, pad_y = 30, 16
    bbox_t = draw.textbbox((0, 0), title, font=font_title)
    w_t = bbox_t[2] - bbox_t[0]
    h_t = bbox_t[3] - bbox_t[1]
    
    w_s, h_s = 0, 0
    if subtitle:
        bbox_s = draw.textbbox((0, 0), subtitle, font=font_sub)
        w_s = bbox_s[2] - bbox_s[0]
        h_s = bbox_s[3] - bbox_s[1] + 8
        
    badge_w = max(w_t, w_s) + pad_x * 2
    badge_h = h_t + h_s + pad_y * 2
    bx = x - badge_w // 2
    by = y - badge_h // 2
    
    # Outer glow / drop shadow
    draw.rounded_rectangle([bx - 2, by - 2, bx + badge_w + 2, by + badge_h + 2], radius=18, outline=(color[0]//2, color[1]//2, color[2]//2, 100), width=4)
    draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=16, fill=bg, outline=color, width=3)
    draw.text((bx + (badge_w - w_t) // 2, by + pad_y), title, font=font_title, fill=color)
    if subtitle:
        draw.text((bx + (badge_w - w_s) // 2, by + pad_y + h_t + 8), subtitle, font=font_sub, fill=(225, 235, 245))

def draw_coiled_spring(draw, p1, p2, coils=8, radius=40, color=(255, 215, 50), width=10):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-3: return
    ux, uy = dx / dist, dy / dist
    nx, ny = -uy, ux
    
    steps = coils * 24
    pts = []
    for i in range(steps + 1):
        t = i / steps
        along = dist * t
        phase = t * coils * 2 * math.pi
        lateral = math.sin(phase) * radius
        px = p1[0] + ux * along + nx * lateral
        py = p1[1] + uy * along + ny * lateral
        pts.append((int(px), int(py)))
        
    # Draw shadow first
    for i in range(len(pts) - 1):
        draw.line([(pts[i][0] + 3, pts[i][1] + 3), (pts[i+1][0] + 3, pts[i+1][1] + 3)],
                  fill=(160, 120, 20), width=width + 2)
    # Core spring
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i+1]], fill=color, width=width)
    # Highlight sheen
    for i in range(len(pts) - 1):
        if i % 8 in [1, 2, 3]:
            draw.line([(pts[i][0] - 2, pts[i][1] - 2), (pts[i+1][0] - 2, pts[i+1][1] - 2)],
                      fill=(255, 255, 220), width=max(2, width // 3))

def draw_lightning_discharge(img_np, p1, p2, color=(0, 255, 255), thickness=4, jitter=25):
    dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    steps = max(5, int(dist / 25))
    pts = [p1]
    dx = (p2[0] - p1[0]) / steps
    dy = (p2[1] - p1[1]) / steps
    
    for i in range(1, steps):
        jx = np.random.uniform(-jitter, jitter)
        jy = np.random.uniform(-jitter, jitter)
        pts.append((int(p1[0] + dx * i + jx), int(p1[1] + dy * i + jy)))
    pts.append(p2)
    
    # Outer glow
    for i in range(len(pts) - 1):
        cv2.line(img_np, pts[i], pts[i+1], (color[0]//3, color[1]//3, color[2]//3), thickness * 4)
    # Main arc
    for i in range(len(pts) - 1):
        cv2.line(img_np, pts[i], pts[i+1], color, thickness)
    # Core white
    for i in range(len(pts) - 1):
        cv2.line(img_np, pts[i], pts[i+1], (255, 255, 255), max(1, thickness // 2))

def save_mp4(frames, filename, fps=FPS):
    out_path = os.path.join(OUTPUT_DIR, filename)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        out_path
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for f in frames:
        if not f.flags["C_CONTIGUOUS"]:
            f = np.ascontiguousarray(f, dtype=np.uint8)
        proc.stdin.write(f.tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"✅ Generated sequence: {filename} ({len(frames)} frames, {len(frames)/fps:.1f}s)", flush=True)
    return out_path


# ==============================================================================
# 1 & 2: FROG ANIMATED SEQUENCES
# ==============================================================================
def render_frog_muscle_compression(num_frames=240):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 20, 28, 255))
        draw = ImageDraw.Draw(img)
        
        # Soft ambient background lighting
        draw.ellipse([WIDTH//2 - 450, HEIGHT//2 - 450, WIDTH//2 + 450, HEIGHT//2 + 450], fill=(22, 35, 48, 255))
        
        # Articulated Frog Head & Oral Cutaway
        # Stage 1: Mouth opens (0.0s - 2.5s)
        # Stage 2: Hyoglossus muscle contracts & compresses spring (2.5s - 5.5s)
        # Stage 3: Maximum 50G potential lock (5.5s - 8.0s)
        
        mouth_open_t = ease_in_out(min(1.0, t * 2.2))
        lower_jaw_y = int(lerp(1020, 1260, mouth_open_t))
        
        # Upper Head (Cel-shaded Green Frog Profile)
        upper_head_pts = [(180, 720), (380, 620), (740, 700), (880, 840), (860, 960), (520, 960), (220, 960)]
        draw.polygon(upper_head_pts, fill=(52, 125, 68), outline=(22, 58, 30), width=8)
        # Specular rim
        draw.line([(220, 720), (380, 630), (730, 710)], fill=(95, 200, 115), width=8)
        # Big Golden Eyeball with horizontal slit pupil
        draw.ellipse([360, 580, 480, 700], fill=(245, 195, 45), outline=(35, 25, 15), width=6)
        draw.ellipse([395, 625, 445, 655], fill=(15, 10, 5))
        
        # Lower Jaw (Articulated Hinge)
        lower_jaw_pts = [(220, 960), (520, lower_jaw_y - 20), (860, lower_jaw_y), (820, lower_jaw_y + 80), (300, 1150)]
        draw.polygon(lower_jaw_pts, fill=(65, 140, 80), outline=(22, 58, 30), width=8)
        
        # Oral Cavity Interior (Deep Maroon/Pink tissue)
        oral_pts = [(520, 960), (840, 960), (840, lower_jaw_y - 10), (520, lower_jaw_y - 10)]
        draw.polygon(oral_pts, fill=(145, 45, 60), outline=(65, 18, 25), width=6)
        
        # Hyoglossus Contractor Muscle Bundle (Dynamic Bulge & Tension)
        compress_t = ease_in_out(clamp((t - 0.25) / 0.50))
        m_start = (530, 1030)
        m_len = int(lerp(380, 180, compress_t))
        m_thick = int(lerp(45, 110, compress_t))
        m_end = (m_start[0] + m_len, 1030)
        
        # Muscle shadow and belly
        draw.ellipse([m_start[0], 1030 - m_thick//2, m_end[0], 1030 + m_thick//2],
                     fill=(195, 35, 55), outline=(100, 15, 25), width=5)
        # Muscle fiber striations
        for s in range(6):
            sx = int(m_start[0] + m_len * (s + 1) / 7)
            draw.line([(sx, 1030 - m_thick//2 + 10), (sx, 1030 + m_thick//2 - 10)],
                      fill=(245, 90, 110), width=5)
                      
        # Collagen Tendon Spring (Gold Coils Compressing)
        spring_start = m_end
        spring_end = (810, 1030)
        draw_coiled_spring(draw, spring_start, spring_end, coils=7, radius=int(lerp(32, 54, compress_t)),
                           color=(255, 215, 50), width=10)
                           
        # Energy Field & Mechanical Latch Icon
        if compress_t > 0.6:
            glow_r = int(lerp(20, 100, (compress_t - 0.6) / 0.4))
            draw.ellipse([spring_end[0] - glow_r - 60, 1030 - glow_r, spring_end[0] + glow_r - 60, 1030 + glow_r],
                         outline=(255, 245, 110, 200), width=5)
            # Tension arrows
            draw.line([(m_end[0] + 40, 950), (m_end[0] - 30, 950)], fill=(255, 100, 100), width=6)
            draw.polygon([(m_end[0] - 40, 950), (m_end[0] - 20, 935), (m_end[0] - 20, 965)], fill=(255, 100, 100))
            
        draw_hud_badge(draw, 540, 340, "HYOGLOSSUS CONTRACTOR MUSCLE", "Contracts backward to load the elastic spring mechanism", color=(255, 100, 120))
        draw_hud_badge(draw, 540, 1580, f"STORED ELASTIC POTENTIAL: {int(compress_t*50):02d}G FORCE",
                       "Mechanical catapult cocked for supersonic launch", color=(255, 215, 0))
                       
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "frog_elastic_muscle_energy_storage.mp4")

def render_frog_tongue_launch(num_frames=270):
    frames = []
    fly_base_x = 900
    fly_base_y = 920
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 20, 28, 255))
        draw = ImageDraw.Draw(img)
        
        # Wide Action Scene:
        # Phase 1 (0.0s - 1.8s): Insect buzzes, frog aims
        # Phase 2 (1.8s - 3.5s): CATAPULT LAUNCH (Extreme 50G acceleration)
        # Phase 3 (3.5s - 5.5s): IMPACT & INVERSION (Saliva shear-thinning adhesion)
        # Phase 4 (5.5s - 9.0s): RECOIL RETRACTION (Snaps back into mouth)
        
        frog_mouth_x, frog_mouth_y = 360, 920
        fly_x = fly_base_x
        fly_y = fly_base_y
        
        # Frog on Left
        frog_pts = [(60, 750), (250, 770), (370, 920), (310, 1150), (120, 1200), (40, 1050)]
        draw.polygon(frog_pts, fill=(52, 125, 68), outline=(22, 58, 30), width=8)
        draw.ellipse([180, 730, 260, 810], fill=(245, 195, 45), outline=(35, 25, 15), width=5)
        draw.ellipse([210, 755, 240, 785], fill=(15, 10, 5))
        
        if t < 0.20:
            tongue_tip = (frog_mouth_x, frog_mouth_y)
        elif t < 0.42:
            launch_t = ease_out_quad((t - 0.20) / 0.22)
            tongue_tip = lerp_pt((frog_mouth_x, frog_mouth_y), (fly_base_x - 30, fly_base_y), launch_t)
        elif t < 0.65:
            tongue_tip = (fly_base_x - 10, fly_base_y)
        else:
            retract_t = ease_in_quad((t - 0.65) / 0.35)
            tongue_tip = lerp_pt((fly_base_x - 10, fly_base_y), (frog_mouth_x, frog_mouth_y), retract_t)
            fly_x = tongue_tip[0] + 20
            fly_y = tongue_tip[1]
            
        # Draw Elastic Tongue Shaft
        if tongue_tip != (frog_mouth_x, frog_mouth_y):
            # Elastic ribbon
            draw.line([(frog_mouth_x, frog_mouth_y), tongue_tip], fill=(235, 75, 105), width=36)
            draw.line([(frog_mouth_x, frog_mouth_y), tongue_tip], fill=(255, 140, 160), width=14)
            # Inverted mushroom pad at tip
            draw.ellipse([tongue_tip[0] - 30, tongue_tip[1] - 40, tongue_tip[0] + 40, tongue_tip[1] + 40],
                         fill=(255, 110, 145), outline=(180, 30, 60), width=5)
                         
        # Insect (Housefly with animated flapping wings)
        draw.ellipse([fly_x - 22, fly_y - 14, fly_x + 22, fly_y + 14], fill=(35, 35, 42), outline=(10, 10, 15), width=3)
        if t < 0.42:
            w_flap = math.sin(fi * 2.2) * 18
            w_top = min(fly_y - 28 + w_flap, fly_y - 10)
            w_bot = max(fly_y - 28 + w_flap, fly_y - 6)
            draw.ellipse([fly_x - 14, int(w_top), fly_x + 12, int(w_bot)], fill=(210, 235, 255, 190))
            
        # Impact Waves & Saliva Viscoelastic Strings
        if 0.40 <= t <= 0.68:
            shock_r = int((t - 0.40) * 550)
            draw.ellipse([fly_base_x - shock_r, fly_base_y - shock_r, fly_base_x + shock_r, fly_base_y + shock_r],
                         outline=(255, 235, 100, max(0, 255 - shock_r * 2)), width=6)
            # Saliva adhesive bridge
            for dy in [-18, 0, 18]:
                draw.line([(tongue_tip[0] + 15, tongue_tip[1] + dy), (fly_x, fly_y + dy)], fill=(245, 245, 190), width=7)
                
        draw_hud_badge(draw, 540, 340, "50-G CATAPULT STRIKE & RECOIL", "Releases in 7ms — mushroom pad inverts upon impact", color=(255, 80, 100))
        if t < 0.42:
            draw_hud_badge(draw, 540, 1580, "ELASTIC SPRING RELEASE: 50G ACCELERATION", color=(255, 215, 0))
        else:
            draw_hud_badge(draw, 540, 1580, "SHEAR-THINNING SALIVA: INSTANT SOLID ADHESION", color=(100, 240, 255))
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "frog_tongue_slingshot_impact_adhesion.mp4")


# ==============================================================================
# 3 & 4: SEA OTTER ANIMATED SEQUENCES
# ==============================================================================
def render_otter_fur_density(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (16, 26, 40, 255))
        draw = ImageDraw.Draw(img)
        
        # Skin Layer at Bottom
        draw.rectangle([0, 1380, WIDTH, HEIGHT], fill=(235, 160, 150), outline=(180, 100, 90), width=6)
        draw.text((WIDTH//2 - 130, 1420), "EPIDERMIS SKIN LAYER", font=get_font(32, bold=True), fill=(140, 60, 50))
        
        # Dense Underfur Shafts
        hair_count = 34
        interlock_t = ease_in_out(clamp((t - 0.30) / 0.50))
        
        for i in range(hair_count):
            hx = int(60 + i * (WIDTH - 120) / (hair_count - 1))
            wave = math.sin(fi * 0.15 + i * 0.35) * 14
            top_x = hx + int(wave + (28 if i % 2 == 0 else -28) * interlock_t)
            top_y = 660 + (i % 3) * 35
            
            # Shaded hair shaft
            draw.line([(hx, 1380), (top_x, top_y)], fill=(120, 80, 50), width=10)
            draw.line([(hx, 1380), (top_x, top_y)], fill=(175, 130, 90), width=4)
            
            # Microscopic Interlocking Barbs
            if interlock_t > 0.1:
                barb_alpha = int(interlock_t * 255)
                for by in range(top_y + 80, 1300, 70):
                    bx = int(lerp(hx, top_x, (1380 - by) / (1380 - top_y)))
                    draw.line([(bx, by), (bx + 18, by - 14)], fill=(215, 175, 130, barb_alpha), width=3)
                    draw.line([(bx, by), (bx - 18, by - 14)], fill=(215, 175, 130, barb_alpha), width=3)
                    
        # Microscopic Zoom Lens Inset
        zoom_cx, zoom_cy = 540, 480
        draw.ellipse([zoom_cx - 240, zoom_cy - 240, zoom_cx + 240, zoom_cy + 240],
                     fill=(24, 38, 55, 245), outline=(255, 215, 80), width=8)
        # Zipper interlocking action inside lens
        z_t = ease_in_out(clamp((t - 0.35) / 0.50))
        d_hook = lerp(70, 0, z_t)
        # Left barb
        draw.line([(zoom_cx - 90 + int(d_hook), zoom_cy - 70), (zoom_cx - 20, zoom_cy)], fill=(215, 165, 115), width=16)
        draw.line([(zoom_cx - 20, zoom_cy), (zoom_cx - 60, zoom_cy + 35)], fill=(215, 165, 115), width=16)
        # Right barb
        draw.line([(zoom_cx + 90 - int(d_hook), zoom_cy + 70), (zoom_cx + 20, zoom_cy)], fill=(175, 125, 85), width=16)
        draw.line([(zoom_cx + 20, zoom_cy), (zoom_cx + 60, zoom_cy - 35)], fill=(175, 125, 85), width=16)
        
        # Digital Counter
        density_num = int(lerp(100000, 1000000, ease_out_quad(min(1.0, t * 1.6))))
        draw_hud_badge(draw, 540, 200, "MICROSCOPIC INTERLOCKING BARBS", "Barbed underfur fibers mechanically zip into an airtight shield", color=(100, 230, 255))
        draw_hud_badge(draw, 540, 1540, f"FUR DENSITY: {density_num:,} HAIRS / IN²",
                       "Densest pelt in the entire animal kingdom", color=(255, 215, 0))
                       
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "otter_fur_density_interlocking_barbs.mp4")

def render_otter_air_bubble_barrier(num_frames=270):
    frames = []
    np.random.seed(42)
    bubbles = [{"x": np.random.randint(120, 960), "y": np.random.randint(920, 1280), "r": np.random.randint(14, 30), "drift": np.random.uniform(0.5, 2.0)} for _ in range(50)]
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (12, 28, 48, 255))
        draw = ImageDraw.Draw(img)
        
        # Upper Freezing Ocean Water
        water_press_y = int(lerp(480, 840, ease_in_out(clamp((t - 0.25) / 0.50))))
        draw.rectangle([0, 0, WIDTH, water_press_y], fill=(20, 58, 98, 255))
        
        # Ice crystals in water
        for ix in range(80, WIDTH - 80, 130):
            iy = (ix * 3 + fi * 4) % (water_press_y - 40)
            draw.polygon([(ix, iy - 14), (ix + 12, iy), (ix, iy + 14), (ix - 12, iy)], fill=(185, 235, 255, 170))
            
        # Dense Interlocked Fur
        draw.rectangle([0, water_press_y, WIDTH, 1420], fill=(78, 52, 38, 255))
        for h in range(42):
            hx = h * 26
            draw.line([(hx, 1420), (hx + int(math.sin(fi * 0.1 + h) * 10), water_press_y)], fill=(135, 95, 65), width=6)
            
        # Trapped Silvery Air Bubbles Cushion
        for b in bubbles:
            by = int(b["y"] + math.sin(fi * 0.12 + b["drift"]) * 8)
            bx = int(b["x"] + math.cos(fi * 0.09 + b["drift"]) * 6)
            if by > water_press_y + 15 and by < 1400:
                draw.ellipse([bx - b["r"], by - b["r"], bx + b["r"], by + b["r"]],
                             fill=(215, 245, 255, 195), outline=(255, 255, 255, 245), width=3)
                draw.ellipse([bx - b["r"]//2, by - b["r"]//2, bx - b["r"]//4, by - b["r"]//4], fill=(255, 255, 255, 255))
                
        # Lower Pink Skin Layer (Warm & 100% Dry)
        draw.rectangle([0, 1420, WIDTH, HEIGHT], fill=(240, 168, 155))
        draw.text((WIDTH//2 - 140, 1470), "WARM SKIN: 37°C", font=get_font(34, bold=True), fill=(160, 50, 40))
        draw.text((WIDTH//2 - 110, 1520), "100% DRY", font=get_font(28, bold=True), fill=(30, 145, 50))
        
        # Deflection boundary sheen
        draw.line([(0, water_press_y), (WIDTH, water_press_y)], fill=(120, 220, 255), width=8)
        
        draw_hud_badge(draw, 540, 320, "FREEZING ARCTIC WATER: 0°C", "Repelled by surface tension of captive bubble layer", color=(120, 225, 255))
        draw_hud_badge(draw, 540, 1680, "CAPTIVE AIR BUBBLE THERMAL DRYSUIT", "Zero body blubber needed — skin never gets wet", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "otter_air_bubble_thermal_barrier.mp4")


# ==============================================================================
# 5 & 6: TRAP-JAW ANT ANIMATED SEQUENCES
# ==============================================================================
def render_ant_muscle_latch(num_frames=255):
    frames = []
    cx, cy = 540, 1100
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (18, 16, 22, 255))
        draw = ImageDraw.Draw(img)
        
        # Head Capsule Dorsal Cutaway
        head_pts = [(cx - 280, cy - 150), (cx + 280, cy - 150), (cx + 340, cy + 220), (cx - 340, cy + 220)]
        draw.polygon(head_pts, fill=(58, 42, 38), outline=(125, 90, 70), width=8)
        
        # Mandible Spread: 30° -> 180° flat
        open_t = ease_in_out(clamp((t - 0.20) / 0.60))
        angle_deg = lerp(35, 90, open_t)
        rad = math.radians(angle_deg)
        
        m_len = 390
        lm_base = (cx - 140, cy - 160)
        rm_base = (cx + 140, cy - 160)
        lm_tip = (int(lm_base[0] - m_len * math.sin(rad)), int(lm_base[1] - m_len * math.cos(rad)))
        rm_tip = (int(rm_base[0] + m_len * math.sin(rad)), int(rm_base[1] - m_len * math.cos(rad)))
        
        # Mandibles with serrated teeth
        draw.line([lm_base, lm_tip], fill=(165, 80, 50), width=30)
        draw.line([rm_base, rm_tip], fill=(165, 80, 50), width=30)
        draw.line([lm_base, lm_tip], fill=(225, 135, 85), width=12)
        draw.line([rm_base, rm_tip], fill=(225, 135, 85), width=12)
        
        # Closer Muscle Swelling & Winching Tendon
        m_thick = int(lerp(45, 115, open_t))
        draw.ellipse([cx - 240, cy - 80, cx - 40, cy - 80 + m_thick * 2], fill=(200, 48, 70), outline=(125, 22, 35), width=5)
        draw.ellipse([cx + 40, cy - 80, cx + 240, cy - 80 + m_thick * 2], fill=(200, 48, 70), outline=(125, 22, 35), width=5)
        
        # Latch Mechanism
        latch_color = (255, 215, 0) if open_t > 0.9 else (180, 180, 180)
        draw.rectangle([cx - 36, cy - 180, cx + 36, cy - 90], fill=latch_color, outline=(40, 40, 40), width=4)
        
        # Trigger Hairs
        draw.line([(cx - 40, cy - 170), (cx - 70, cy - 350)], fill=(245, 245, 245), width=4)
        draw.line([(cx + 40, cy - 170), (cx + 70, cy - 350)], fill=(245, 245, 245), width=4)
        
        draw_hud_badge(draw, 540, 340, "MASSIVE CLOSER MUSCLES WINCH SPRING", "Contraction locks mandibles flat at 180 degrees", color=(255, 100, 120))
        draw_hud_badge(draw, 540, 1550, f"MANDIBLE SPREAD: {int(angle_deg*2):03d}°",
                       "Spring latch engages when fully cocked" if open_t < 0.9 else "🔒 LATCH LOCKED (READY TO STRIKE)",
                       color=(255, 215, 0) if open_t > 0.9 else (200, 225, 255))
                       
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "trap_jaw_ant_muscle_latch_mechanism.mp4")

def render_ant_explosive_strike(num_frames=285):
    frames = []
    cx, cy = 540, 1100
    prey_y = 700
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (18, 16, 22, 255))
        draw = ImageDraw.Draw(img)
        
        recoil_y = 0
        if t >= 0.70:
            jump_t = (t - 0.70) / 0.30
            recoil_y = int(math.sin(jump_t * math.pi) * 480)
            
        cur_cy = cy + recoil_y
        
        if t < 0.30:
            angle_deg = 90
        elif t < 0.36:
            snap_t = ease_in_quad((t - 0.30) / 0.06)
            angle_deg = lerp(90, 8, snap_t)
        else:
            angle_deg = 8
            
        rad = math.radians(angle_deg)
        m_len = 390
        lm_base = (cx - 140, cur_cy - 160)
        rm_base = (cx + 140, cur_cy - 160)
        lm_tip = (int(lm_base[0] - m_len * math.sin(rad)), int(lm_base[1] - m_len * math.cos(rad)))
        rm_tip = (int(rm_base[0] + m_len * math.sin(rad)), int(rm_base[1] - m_len * math.cos(rad)))
        
        # Head
        draw.polygon([(cx - 280, cur_cy - 150), (cx + 280, cur_cy - 150), (cx + 340, cur_cy + 220), (cx - 340, cur_cy + 220)],
                     fill=(58, 42, 38), outline=(125, 90, 70), width=8)
        draw.line([lm_base, lm_tip], fill=(225, 135, 85), width=26)
        draw.line([rm_base, rm_tip], fill=(225, 135, 85), width=26)
        
        # Prey Insect
        if t < 0.35:
            draw.ellipse([cx - 42, prey_y - 32, cx + 42, prey_y + 32], fill=(90, 145, 70), outline=(45, 80, 35), width=4)
        else:
            split_d = int((t - 0.35) * 650)
            draw.ellipse([cx - 65 - split_d, prey_y - 32, cx - split_d, prey_y + 32], fill=(90, 145, 70))
            draw.ellipse([cx + split_d, prey_y - 32, cx + 65 + split_d, prey_y + 32], fill=(90, 145, 70))
            
        # Supersonic Shockwave Ring
        if 0.33 <= t <= 0.65:
            sw_r = int((t - 0.33) * 1100)
            draw.ellipse([cx - sw_r, prey_y - sw_r//2, cx + sw_r, prey_y + sw_r//2],
                         outline=(255, 235, 100, max(0, 255 - sw_r // 3)), width=8)
            for sp in range(8):
                sx = cx + int(math.cos(sp) * sw_r * 0.7)
                sy = prey_y + int(math.sin(sp) * sw_r * 0.4)
                draw.line([(cx, prey_y), (sx, sy)], fill=(255, 255, 210), width=3)
                
        draw_hud_badge(draw, 540, 340, "140 MPH SUPERSONIC STRIKE", "Snaps shut in 0.1ms — 2,300x faster than an eye blink", color=(255, 80, 80))
        if t < 0.70:
            draw_hud_badge(draw, 540, 1550, "TRIGGER HAIR TOUCH -> EXPLOSIVE ELASTIC RELEASE", color=(255, 215, 0))
        else:
            draw_hud_badge(draw, 540, 1550, "GROUND REACTION: ESCAPE LAUNCH 40CM AIRBORNE", color=(100, 235, 255))
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "trap_jaw_ant_explosive_mandible_strike.mp4")


# ==============================================================================
# 7 & 8: PIT VIPER ANIMATED SEQUENCES
# ==============================================================================
def render_viper_loreal_pit(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (15, 19, 24, 255))
        draw = ImageDraw.Draw(img)
        
        # Viper Profile
        v_pts = [(180, 650), (450, 580), (880, 720), (950, 920), (820, 1080), (400, 1100), (180, 980)]
        draw.polygon(v_pts, fill=(52, 98, 58), outline=(26, 58, 32), width=8)
        draw.ellipse([700, 680, 790, 770], fill=(230, 180, 38), outline=(32, 22, 12), width=5)
        draw.line([(745, 685), (745, 765)], fill=(10, 5, 5), width=8)
        
        # Loreal Pit
        pit_x, pit_y = 820, 810
        draw.ellipse([pit_x - 32, pit_y - 26, pit_x + 32, pit_y + 26], fill=(22, 28, 28), outline=(155, 205, 85), width=4)
        
        # Microscopic Cutaway Chamber
        cx, cy = 540, 1200
        draw.ellipse([cx - 320, cy - 220, cx + 320, cy + 220], fill=(26, 34, 42), outline=(255, 215, 0), width=6)
        draw.chord([cx - 280, cy - 180, cx + 280, cy + 180], start=90, end=270, fill=(38, 48, 58))
        draw.chord([cx - 280, cy - 180, cx + 280, cy + 180], start=270, end=90, fill=(16, 22, 28))
        
        # Suspended 15μm Membrane vibrating
        vib = math.sin(fi * 0.4) * 6
        draw.line([(cx + int(vib), cy - 170), (cx + int(vib), cy + 170)], fill=(255, 105, 125), width=8)
        for my in range(cy - 140, cy + 150, 35):
            draw.ellipse([cx - 8 + int(vib), my - 8, cx + 8 + int(vib), my + 8], fill=(255, 235, 85))
            
        draw_hud_badge(draw, 540, 340, "LOREAL FACIAL PIT CAVITY", "Stereoscopic thermal sensory chambers between eye and nostril", color=(100, 240, 255))
        draw_hud_badge(draw, 540, 1540, "15-MICROMETER SUSPENDED MEMBRANE", "Packed with TRPA1 infrared-sensitive ion channel receptors", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "pit_viper_loreal_pit_anatomy.mp4")

def render_viper_pinhole_thermal(num_frames=270):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (10, 12, 18, 255))
        draw = ImageDraw.Draw(img)
        
        mouse_x = 220
        mouse_y = int(850 + math.sin(fi * 0.08) * 20)
        
        # Mouse Thermal Silhouette
        draw.ellipse([mouse_x - 90, mouse_y - 50, mouse_x + 90, mouse_y + 50], fill=(255, 65, 25))
        draw.ellipse([mouse_x + 50, mouse_y - 45, mouse_x + 110, mouse_y + 5], fill=(255, 165, 35))
        draw.ellipse([mouse_x + 70, mouse_y - 20, mouse_x + 90, mouse_y], fill=(255, 245, 85))
        draw.line([(mouse_x - 90, mouse_y), (mouse_x - 160, mouse_y + 40)], fill=(205, 45, 25), width=6)
        
        # Radiating IR Waves
        for w in range(4):
            wr = int((fi * 8 + w * 120) % 500)
            draw.arc([mouse_x - wr, mouse_y - wr, mouse_x + wr, mouse_y + wr],
                     start=-45, end=45, fill=(255, 85, 25, max(0, 200 - wr // 2)), width=5)
                     
        pinhole_x, pinhole_y = 650, 850
        membrane_x = 880
        
        # Pinhole Aperture
        draw.rectangle([pinhole_x, 500, pinhole_x + 40, pinhole_y - 40], fill=(85, 115, 80))
        draw.rectangle([pinhole_x, pinhole_y + 40, pinhole_x + 40, 1200], fill=(85, 115, 80))
        draw.line([(membrane_x, 600), (membrane_x, 1100)], fill=(125, 165, 205), width=10)
        
        # Camera Obscura Rays
        draw.line([(mouse_x + 70, mouse_y - 40), (pinhole_x + 20, pinhole_y), (membrane_x, 1020)],
                  fill=(255, 225, 85, 225), width=4)
        draw.line([(mouse_x + 70, mouse_y + 40), (pinhole_x + 20, pinhole_y), (membrane_x, 680)],
                  fill=(255, 75, 35, 225), width=4)
                  
        # Inverted Thermal Image
        draw.ellipse([membrane_x - 20, 800, membrane_x + 20, 900], fill=(255, 125, 35))
        draw.ellipse([membrane_x - 15, 740, membrane_x + 15, 800], fill=(255, 235, 65))
        
        draw_hud_badge(draw, 540, 340, "PINHOLE CAMERA OBSCURA EFFECT", "Narrow pit aperture optically refracts infrared rays", color=(255, 165, 45))
        draw_hud_badge(draw, 540, 1540, "INVERTED THERMAL HEATMAP PROJECTION", "Trigeminal nerve superimposes heat map over vision", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "pit_viper_pinhole_thermal_projection.mp4")


# ==============================================================================
# 9 & 10: ARCHERFISH ANIMATED SEQUENCES
# ==============================================================================
def render_archerfish_palate_tongue(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 30, 50, 255))
        draw = ImageDraw.Draw(img)
        
        water_surface_y = 650
        draw.rectangle([0, 0, WIDTH, water_surface_y], fill=(18, 24, 34, 255))
        draw.rectangle([0, water_surface_y, WIDTH, HEIGHT], fill=(22, 58, 95, 255))
        draw.line([(0, water_surface_y), (WIDTH, water_surface_y)], fill=(125, 215, 255), width=5)
        
        cx, cy = 450, 1050
        fish_pts = [(cx - 280, cy + 180), (cx + 180, cy - 140), (cx + 320, cy - 80), (cx + 120, cy + 320)]
        draw.polygon(fish_pts, fill=(190, 200, 165), outline=(42, 52, 38), width=8)
        draw.line([(cx - 80, cy - 30), (cx - 20, cy + 220)], fill=(32, 38, 28), width=32)
        
        draw.ellipse([cx + 60, cy - 120, cx + 150, cy - 30], fill=(250, 220, 45), outline=(22, 22, 12), width=5)
        draw.ellipse([cx + 90, cy - 100, cx + 130, cy - 60], fill=(10, 10, 10))
        
        # Palate & Grooved Tongue Rifle Tube
        press_t = ease_in_out(clamp((t - 0.25) / 0.50))
        tongue_y = int(lerp(cy + 60, cy + 5, press_t))
        palate_y = cy
        
        draw.line([(cx + 160, palate_y - 20), (cx + 300, palate_y - 65)], fill=(225, 125, 135), width=16)
        draw.line([(cx + 160, tongue_y + 10), (cx + 290, tongue_y - 35)], fill=(245, 165, 165), width=18)
        
        if press_t > 0.4:
            draw.line([(cx + 170, cy - 5), (cx + 295, cy - 50)], fill=(105, 235, 255), width=10)
            
        gill_squeeze = int(lerp(0, 35, press_t))
        draw.arc([cx - 140 + gill_squeeze, cy + 20, cx - 40, cy + 180], start=90, end=270, fill=(245, 85, 85), width=8)
        
        draw_hud_badge(draw, 540, 340, "GROOVED TONGUE + ROOF PALATE", "Press together to seal a rigid cylindrical rifle barrel", color=(255, 215, 0))
        draw_hud_badge(draw, 540, 1550, "HYDRAULIC GILL PISTON COMPRESSION", "Gill covers squeeze shut to pressurize the water chamber", color=(100, 230, 255))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "archerfish_palate_tongue_rifle_barrel.mp4")

def render_archerfish_water_bullet(num_frames=270):
    frames = []
    branch_x, branch_y = 880, 480
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (16, 22, 32, 255))
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([0, 1400, WIDTH, HEIGHT], fill=(22, 62, 110, 255))
        draw.line([(0, 1400), (WIDTH, 1400)], fill=(125, 225, 255), width=5)
        draw.line([(branch_x - 300, branch_y + 120), (WIDTH, branch_y - 50)], fill=(95, 70, 50), width=28)
        
        gh_alive = t < 0.60
        gh_x = branch_x - 80
        gh_y = branch_y + 15
        if not gh_alive:
            fall_t = (t - 0.60) / 0.40
            gh_x += int(fall_t * 60)
            gh_y += int(fall_t * fall_t * 920)
            
        draw.ellipse([gh_x - 30, gh_y - 15, gh_x + 30, gh_y + 15], fill=(75, 180, 60), outline=(32, 98, 28), width=4)
        
        mouth_x, mouth_y = 260, 1380
        target = (branch_x - 90, branch_y + 15)
        
        if t < 0.20:
            bullet_pos = (mouth_x, mouth_y)
        elif t < 0.60:
            flight_t = (t - 0.20) / 0.40
            bullet_pos = lerp_pt((mouth_x, mouth_y), target, ease_out_quad(flight_t))
            draw.line([(mouth_x, mouth_y), bullet_pos], fill=(125, 215, 255, 165), width=int(lerp(6, 22, flight_t)))
            drop_r = int(lerp(12, 38, flight_t))
            draw.ellipse([bullet_pos[0] - drop_r, bullet_pos[1] - drop_r, bullet_pos[0] + drop_r, bullet_pos[1] + drop_r],
                         fill=(185, 245, 255, 240), outline=(255, 255, 255), width=4)
        else:
            bullet_pos = target
            spl_t = (t - 0.60) / 0.40
            for sp in range(12):
                ang = sp * (2 * math.pi / 12)
                sp_d = int(spl_t * 360)
                sx = target[0] + int(math.cos(ang) * sp_d)
                sy = target[1] + int(math.sin(ang) * sp_d * 0.7)
                draw.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], fill=(185, 240, 255, max(0, 255 - sp_d)))
                
        draw_hud_badge(draw, 540, 320, "MID-AIR WATER BULLET COALESCENCE", "Trailing water moves faster than front, bunching into a slug", color=(100, 230, 255))
        if t < 0.60:
            draw_hud_badge(draw, 540, 1550, "VELOCITY: 5 M/S -> IMPACT MASS CONCENTRATION", color=(255, 215, 0))
        else:
            draw_hud_badge(draw, 540, 1550, "6X KINETIC FORCE KNOCKS PREY OFF PERCH", color=(255, 100, 100))
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "archerfish_water_bullet_coalescence_strike.mp4")


# ==============================================================================
# 11 & 12: CROCODILE ANIMATED SEQUENCES
# ==============================================================================
def render_crocodile_jaw_muscle_bite(num_frames=255):
    frames = []
    cx, cy = 420, 950
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (20, 24, 22, 255))
        draw = ImageDraw.Draw(img)
        
        clamp_t = ease_in_out(clamp((t - 0.25) / 0.45))
        gape_deg = lerp(40, 4, clamp_t)
        rad = math.radians(gape_deg)
        
        upper_pts = [(cx - 250, cy - 120), (cx + 420, cy - 40), (cx + 440, cy), (cx - 200, cy + 20)]
        draw.polygon(upper_pts, fill=(58, 78, 64), outline=(26, 42, 32), width=8)
        
        low_end_x = int(cx + 430 * math.cos(rad))
        low_end_y = int(cy + 430 * math.sin(rad))
        draw.line([(cx - 200, cy + 40), (low_end_x, low_end_y)], fill=(78, 98, 74), width=42)
        
        for tx in range(cx - 100, cx + 400, 55):
            draw.polygon([(tx, cy), (tx + 12, cy + 28), (tx - 12, cy + 28)], fill=(245, 245, 235))
            draw.polygon([(tx + 25, low_end_y), (tx + 37, low_end_y - 28), (tx + 13, low_end_y - 28)], fill=(245, 245, 235))
            
        m_thick = int(lerp(55, 145, clamp_t))
        draw.ellipse([cx - 220, cy - 100, cx - 20, cy - 100 + m_thick * 2], fill=(190, 42, 58), outline=(115, 22, 32), width=6)
        
        if clamp_t > 0.95:
            shake = int(math.sin(fi * 2.0) * 8)
            draw.line([(cx + 380 + shake, cy - 60), (cx + 380 + shake, cy + 60)], fill=(255, 235, 85), width=8)
            
        draw_hud_badge(draw, 540, 340, "MASSIVE PTERYGOID CLOSER MUSCLES", "Fill the rear skull to generate 3,700 lbs crushing force", color=(255, 100, 120))
        draw_hud_badge(draw, 540, 1550, f"BITE PRESSURE: {int(clamp_t*3700):,d} LBS/IN²",
                       "Conical teeth lock prey with zero lateral chewing motion", color=(255, 215, 0))
                       
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "crocodile_pterygoid_jaw_muscle_bite.mp4")

def render_crocodile_death_roll(num_frames=285):
    frames = []
    cx, cy = 540, 960
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 38, 58, 255))
        draw = ImageDraw.Draw(img)
        
        spin_t = ease_in_quad(clamp((t - 0.20) / 0.60))
        angle = fi * (0.1 + spin_t * 0.7)
        
        for vr in range(120, 600, 90):
            rot_r = int((angle * 40 + vr) % 600)
            alpha = int(max(0, min(255, 180 - rot_r // 3)))
            draw.ellipse([cx - rot_r, cy - rot_r//2, cx + rot_r, cy + rot_r//2],
                         outline=(85, 185, 240, alpha), width=6)
                         
        body_w = int(240 + math.cos(angle) * 80)
        body_h = int(120 + math.sin(angle) * 60)
        
        draw.ellipse([cx - body_w, cy - body_h, cx + body_w, cy + body_h], fill=(48, 78, 58), outline=(22, 42, 28), width=8)
        draw.arc([cx - 350, cy - 250, cx + 350, cy + 250], start=int(math.degrees(angle)), end=int(math.degrees(angle) + 120),
                 fill=(205, 245, 255), width=12)
                 
        draw_hud_badge(draw, 540, 340, "ROTATIONAL INERTIA REDUCTION", "Tucks limbs against torso to spin like a high-speed drill", color=(100, 230, 255))
        draw_hud_badge(draw, 540, 1550, f"DEATH ROLL ROTATION: {int(spin_t*300):03d} RPM",
                       "Rotational shear torque tears meat along anatomical fault lines", color=(255, 215, 0))
                       
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "crocodile_death_roll_rotational_inertia.mp4")


# ==============================================================================
# 13 & 14: ELECTRIC EEL ANIMATED SEQUENCES
# ==============================================================================
def render_eel_electrocyte_stacks(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (12, 24, 38, 255))
        draw = ImageDraw.Draw(img)
        
        draw.rounded_rectangle([180, 500, WIDTH - 180, 1400], radius=80, fill=(28, 48, 64), outline=(55, 95, 125), width=6)
        
        cols = 5
        discs_per_col = 22
        for c in range(cols):
            col_x = 260 + c * 135
            for d in range(discs_per_col):
                col_y = 560 + d * 36
                draw.ellipse([col_x - 45, col_y - 12, col_x + 45, col_y + 12],
                             fill=(65, 115, 150), outline=(125, 205, 245), width=2)
                             
        zoom_cx, zoom_cy = 540, 1250
        draw.ellipse([zoom_cx - 250, zoom_cy - 120, zoom_cx + 250, zoom_cy + 120],
                     fill=(22, 38, 54), outline=(255, 215, 0), width=6)
        draw.text((zoom_cx - 160, zoom_cy - 20), "INACTIVE (-)", font=get_font(28, bold=True), fill=(145, 185, 225))
        draw.text((zoom_cx + 60, zoom_cy - 20), "SODIUM Na+", font=get_font(28, bold=True), fill=(255, 205, 65))
        
        draw_hud_badge(draw, 540, 320, "6,000 ELECTROCYTES IN SERIES", "Occupies over 80% of the entire body volume", color=(100, 230, 255))
        draw_hud_badge(draw, 540, 1550, "STACKED LIKE ROLLS OF COINS", "Each disc cell produces 0.15 volts at rest", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "electric_eel_electrocyte_stack_columns.mp4")

def render_eel_lightning_discharge(num_frames=285):
    frames = []
    np.random.seed(42)
    for fi in range(num_frames):
        t = fi / num_frames
        img_np = np.full((HEIGHT, WIDTH, 3), (14, 20, 28), dtype=np.uint8)
        
        eel_y1, eel_y2 = 450, 1350
        cv2.rectangle(img_np, (350, eel_y1), (730, eel_y2), (48, 68, 85), -1)
        cv2.rectangle(img_np, (350, eel_y1), (730, eel_y2), (125, 185, 225), 4)
        
        discharge_t = ease_in_quad(clamp((t - 0.25) / 0.50))
        voltage = int(discharge_t * 860)
        
        if discharge_t > 0.4:
            num_bolts = int(lerp(2, 9, (discharge_t - 0.4) / 0.6))
            for b in range(num_bolts):
                p1 = (np.random.randint(380, 700), np.random.randint(eel_y1 + 50, eel_y2 - 50))
                p2 = (np.random.choice([np.random.randint(40, 250), np.random.randint(830, 1040)]),
                      np.random.randint(300, 1600))
                draw_lightning_discharge(img_np, p1, p2, color=(255, 255, 0), thickness=np.random.randint(3, 7))
                
        img_pil = Image.fromarray(img_np)
        draw = ImageDraw.Draw(img_pil)
        
        draw_hud_badge(draw, 540, 320, "SERIES VOLTAGE MULTIPLICATION", "0.15V x 6,000 cells synchronizing in 1 millisecond", color=(100, 240, 255))
        draw_hud_badge(draw, 540, 1550, f"VOLTAGE DISCHARGE: {voltage:03d} VOLTS",
                       "Enough electrical power to stun an adult horse" if voltage > 600 else "Sodium ion channels opening in series",
                       color=(255, 235, 50) if voltage > 600 else (200, 225, 255))
                       
        frames.append(cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR))
    return save_mp4(frames, "electric_eel_series_voltage_lightning_discharge.mp4")


# ==============================================================================
# MAIN BATCH EXECUTION
# ==============================================================================
def render_all():
    print("🚀 Rendering all 14 master realistic cartoon animation sequences...", flush=True)
    animations = [
        ("Frog Muscle Compression", render_frog_muscle_compression),
        ("Frog Tongue Launch", render_frog_tongue_launch),
        ("Otter Fur Density", render_otter_fur_density),
        ("Otter Air Bubble Barrier", render_otter_air_bubble_barrier),
        ("Ant Muscle Latch", render_ant_muscle_latch),
        ("Ant Explosive Strike", render_ant_explosive_strike),
        ("Pit Viper Loreal Pit", render_viper_loreal_pit),
        ("Pit Viper Pinhole Thermal", render_viper_pinhole_thermal),
        ("Archerfish Palate Tongue", render_archerfish_palate_tongue),
        ("Archerfish Water Bullet", render_archerfish_water_bullet),
        ("Crocodile Jaw Muscle Bite", render_crocodile_jaw_muscle_bite),
        ("Crocodile Death Roll", render_crocodile_death_roll),
        ("Electric Eel Electrocyte Stacks", render_eel_electrocyte_stacks),
        ("Electric Eel Lightning Discharge", render_eel_lightning_discharge),
    ]
    for idx, (name, fn) in enumerate(animations, 1):
        print(f"🎬 [{idx}/14] Rendering {name}...", flush=True)
        fn()
    print("🎉 All 14 master realistic cartoon animations rendered successfully!", flush=True)

if __name__ == "__main__":
    render_all()
