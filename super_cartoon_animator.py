"""
Super Realistic Educational Cartoon Animation Engine (Kurzgesagt / TED-Ed Style)
100% Procedural Vector Animation — Zero Static Images.
Features rich environmental backgrounds, organic multi-tone cel-shaded characters,
articulated anatomical mechanisms, particle physics, and scientific HUD telemetry.
"""

import math
import os
import subprocess
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920
FPS = 30
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================================================
# Math, Geometry & Spline Primitives
# ==============================================================================
def clamp(v, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, float(v)))

def ease_in_out(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)

def ease_out_quad(t):
    t = clamp(t)
    return 1.0 - (1.0 - t) * (1.0 - t)

def ease_in_quad(t):
    t = clamp(t)
    return t * t

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_pt(p1, p2, t):
    return (int(lerp(p1[0], p2[0], t)), int(lerp(p1[1], p2[1], t)))

def rotate_pt(pt, origin, angle_rad):
    ox, oy = origin
    px, py = pt
    qx = ox + math.cos(angle_rad) * (px - ox) - math.sin(angle_rad) * (py - oy)
    qy = oy + math.sin(angle_rad) * (px - ox) + math.cos(angle_rad) * (py - oy)
    return (int(qx), int(qy))

def cubic_bezier(p0, p1, p2, p3, steps=30):
    pts = []
    for t in np.linspace(0, 1, steps):
        x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
        pts.append((int(x), int(y)))
    return pts

def get_font(size=36, bold=True):
    try:
        font_path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def draw_hud(draw, x, y, title, subtitle="", color=(255, 215, 0), bg=(14, 20, 30, 240)):
    font_title = get_font(34, bold=True)
    font_sub = get_font(26, bold=False)
    
    pad_x, pad_y = 34, 18
    bbox_t = draw.textbbox((0, 0), title, font=font_title)
    w_t = bbox_t[2] - bbox_t[0]
    h_t = bbox_t[3] - bbox_t[1]
    
    w_s, h_s = 0, 0
    if subtitle:
        bbox_s = draw.textbbox((0, 0), subtitle, font=font_sub)
        w_s = bbox_s[2] - bbox_s[0]
        h_s = bbox_s[3] - bbox_s[1] + 10
        
    badge_w = max(w_t, w_s) + pad_x * 2
    badge_h = h_t + h_s + pad_y * 2
    bx = x - badge_w // 2
    by = y - badge_h // 2
    
    # Outer glow & glassmorphism card
    draw.rounded_rectangle([bx - 3, by - 3, bx + badge_w + 3, by + badge_h + 3], radius=18, outline=(color[0]//2, color[1]//2, color[2]//2, 110), width=4)
    draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=16, fill=bg, outline=color, width=3)
    
    # Text
    draw.text((bx + (badge_w - w_t) // 2, by + pad_y), title, font=font_title, fill=color)
    if subtitle:
        draw.text((bx + (badge_w - w_s) // 2, by + pad_y + h_t + 8), subtitle, font=font_sub, fill=(225, 235, 245))

def draw_coiled_spring(draw, p1, p2, coils=8, radius=44, color=(255, 215, 50), width=10):
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
        
    for i in range(len(pts) - 1):
        draw.line([(pts[i][0] + 3, pts[i][1] + 3), (pts[i+1][0] + 3, pts[i+1][1] + 3)],
                  fill=(130, 95, 18), width=width + 2)
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i+1]], fill=color, width=width)
    for i in range(len(pts) - 1):
        if i % 6 in [1, 2]:
            draw.line([(pts[i][0] - 2, pts[i][1] - 2), (pts[i+1][0] - 2, pts[i+1][1] - 2)],
                      fill=(255, 255, 220), width=max(2, width // 3))

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
# BACKGROUND ENVIRONMENT DRAWING HELPERS
# ==============================================================================
def draw_jungle_background(draw, t=0.0):
    # Rich rainforest twilight gradient
    for y in range(0, HEIGHT, 16):
        ty = y / HEIGHT
        r = int(lerp(12, 22, ty))
        g = int(lerp(28, 54, ty))
        b = int(lerp(38, 48, ty))
        draw.rectangle([0, y, WIDTH, y + 16], fill=(r, g, b, 255))
        
    # Large tropical background foliage (Monstera leaves)
    leaf1 = cubic_bezier((0, 300), (220, 260), (320, 480), (140, 680), steps=20)
    leaf1.extend(cubic_bezier((140, 680), (60, 580), (0, 450), (0, 300), steps=15))
    draw.polygon(leaf1, fill=(18, 48, 32), outline=(10, 32, 20), width=4)
    
    leaf2 = cubic_bezier((WIDTH, 200), (WIDTH - 250, 180), (WIDTH - 360, 420), (WIDTH - 160, 620), steps=20)
    leaf2.extend(cubic_bezier((WIDTH - 160, 620), (WIDTH - 80, 520), (WIDTH, 380), (WIDTH, 200), steps=15))
    draw.polygon(leaf2, fill=(16, 44, 30), outline=(10, 32, 20), width=4)
    
    # Soft sunbeams filtering through canopy
    draw.polygon([(200, 0), (380, 0), (650, HEIGHT), (420, HEIGHT)], fill=(255, 255, 200, 12))
    draw.polygon([(520, 0), (680, 0), (950, HEIGHT), (760, HEIGHT)], fill=(255, 255, 200, 10))

def draw_ocean_background(draw, t=0.0):
    # Freezing Arctic ocean gradient
    for y in range(0, HEIGHT, 16):
        ty = y / HEIGHT
        r = int(lerp(8, 16, ty))
        g = int(lerp(24, 48, ty))
        b = int(lerp(48, 85, ty))
        draw.rectangle([0, y, WIDTH, y + 16], fill=(r, g, b, 255))
        
    # Floating icebergs in background
    ice_pts = [(120, 480), (240, 380), (340, 440), (420, 410), (520, 500)]
    draw.polygon(ice_pts, fill=(165, 215, 240, 160), outline=(210, 245, 255, 200), width=3)
    
    # Submerged kelp strands swaying
    for k in range(5):
        kx = 150 + k * 180
        sway = math.sin(t * 4.0 + k) * 35
        pts = cubic_bezier((kx, HEIGHT), (kx + int(sway*0.4), HEIGHT - 300), (kx - int(sway*0.7), HEIGHT - 700), (kx + int(sway), HEIGHT - 1100), steps=25)
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(22, 65, 45, 120), width=24)


# ==============================================================================
# 1 & 2: FROG ANIMATIONS (KURZEGSAGT / TED-ED CARTOON)
# ==============================================================================
def render_frog_muscle_compression(num_frames=240):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 20, 28, 255))
        draw = ImageDraw.Draw(img)
        draw_jungle_background(draw, t)
        
        # Mossy tree branch frog perches on
        branch_pts = cubic_bezier((0, 1180), (380, 1140), (740, 1180), (WIDTH, 1220), steps=20)
        for i in range(len(branch_pts) - 1):
            draw.line([(branch_pts[i][0], branch_pts[i][1] + 10), (branch_pts[i+1][0], branch_pts[i+1][1] + 10)], fill=(65, 48, 32), width=70)
            draw.line([branch_pts[i], branch_pts[i+1]], fill=(105, 78, 52), width=60)
            draw.line([(branch_pts[i][0], branch_pts[i][1] - 15), (branch_pts[i+1][0], branch_pts[i+1][1] - 15)], fill=(75, 125, 55), width=18)
            
        # Frog Body & Skull Pivot
        pivot = (340, 930)
        gape_t = ease_in_out(min(1.0, t * 2.2))
        jaw_angle = lerp(0.0, 34.0, gape_t)
        jaw_rad = math.radians(jaw_angle)
        
        # Frog Hindquarters & Belly
        belly_pts = cubic_bezier((120, 1140), (100, 960), (160, 840), (280, 840), steps=15)
        belly_pts.extend(cubic_bezier((280, 840), (360, 980), (340, 1140), (120, 1140), steps=15))
        draw.polygon(belly_pts, fill=(62, 155, 80), outline=(28, 75, 38), width=8)
        # Yellow flank stripe
        draw.ellipse([140, 920, 220, 1080], fill=(235, 205, 50))
        
        # Upper Cranium & Snout (Organic Bezier Profile)
        cranial = cubic_bezier((200, 930), (200, 720), (340, 600), (520, 600), steps=20)
        cranial.extend(cubic_bezier((520, 600), (680, 600), (820, 720), (880, 880), steps=20))
        cranial.extend(cubic_bezier((880, 880), (900, 930), (860, 930), (800, 930), steps=10))
        cranial.append(pivot)
        cranial.append((200, 930))
        draw.polygon(cranial, fill=(58, 148, 75), outline=(24, 68, 34), width=8)
        
        # Golden Eyeball with Iris Gradient & Specular Glint
        eye_cx, eye_cy = 580, 660
        draw.ellipse([eye_cx - 85, eye_cy - 85, eye_cx + 85, eye_cy + 85], fill=(250, 195, 35), outline=(30, 22, 10), width=8)
        draw.ellipse([eye_cx - 55, eye_cy - 22, eye_cx + 55, eye_cy + 22], fill=(18, 12, 6)) # Slit pupil
        draw.ellipse([eye_cx - 40, eye_cy - 55, eye_cx - 15, eye_cy - 30], fill=(255, 255, 255)) # Glint
        draw.ellipse([eye_cx + 20, eye_cy - 35, eye_cx + 38, eye_cy - 18], fill=(255, 255, 255))
        
        # Tympanic membrane (ear disc)
        draw.ellipse([380, 760, 460, 840], fill=(92, 125, 70), outline=(38, 65, 28), width=5)
        
        # Articulated Lower Jaw
        low_base = [(pivot[0], pivot[1]), (pivot[0] + 530, pivot[1]), (pivot[0] + 490, pivot[1] + 110), (pivot[0] - 60, pivot[1] + 160)]
        low_rot = [rotate_pt(p, pivot, jaw_rad) for p in low_base]
        draw.polygon(low_rot, fill=(72, 165, 88), outline=(24, 68, 34), width=8)
        
        # Oral Mucosa Cavity
        oral_pts = [pivot, (pivot[0] + 510, pivot[1]), low_rot[1]]
        draw.polygon(oral_pts, fill=(155, 45, 65), outline=(78, 18, 28), width=6)
        
        # Hyoglossus Contractor Muscle Bundle (Bulging & winching backward)
        compress_t = ease_in_out(clamp((t - 0.25) / 0.50))
        m_start = (pivot[0] + 40, pivot[1] + 25)
        m_len = int(lerp(390, 170, compress_t))
        m_thick = int(lerp(48, 125, compress_t))
        m_end = (m_start[0] + m_len, m_start[1])
        
        # Muscle belly
        draw.ellipse([m_start[0], m_start[1] - m_thick//2, m_end[0], m_start[1] + m_thick//2],
                     fill=(218, 40, 65), outline=(115, 18, 30), width=6)
        # Striated muscle fibers
        for s in range(7):
            sx = int(m_start[0] + m_len * (s + 1) / 8)
            draw.line([(sx, m_start[1] - m_thick//2 + 10), (sx, m_start[1] + m_thick//2 - 10)],
                      fill=(255, 120, 140), width=5)
                      
        # Collagen Spring Coils (Compressing tightly)
        spring_start = m_end
        spring_end = (low_rot[1][0] - 40, low_rot[1][1] - 30)
        spring_rad = int(lerp(34, 56, compress_t))
        draw_coiled_spring(draw, spring_start, spring_end, coils=7, radius=spring_rad, color=(255, 215, 50), width=10)
        
        # Tension Force Vectors
        if compress_t > 0.6:
            pulse = math.sin(fi * 0.8) * 16
            draw.ellipse([spring_end[0] - 50 - int(pulse), spring_end[1] - 50 - int(pulse),
                          spring_end[0] + 50 + int(pulse), spring_end[1] + 50 + int(pulse)],
                         outline=(255, 245, 110, 220), width=5)
            draw.line([(m_end[0] + 50, m_start[1] - 90), (m_end[0] - 30, m_start[1] - 90)], fill=(255, 90, 90), width=7)
            draw.polygon([(m_end[0] - 40, m_start[1] - 90), (m_end[0] - 20, m_start[1] - 105), (m_end[0] - 20, m_start[1] - 75)], fill=(255, 90, 90))
            
        draw_hud(draw, 540, 320, "HYOGLOSSUS CONTRACTOR MUSCLE", "Contracts backward to winch the coiled collagen spring", color=(255, 100, 120))
        draw_hud(draw, 540, 1600, f"STORED ELASTIC POTENTIAL: {int(compress_t*50):02d}G FORCE",
                 "Mechanical catapult cocked for supersonic release", color=(255, 215, 0))
                 
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "frog_elastic_muscle_energy_storage.mp4")

def render_frog_tongue_launch(num_frames=270):
    frames = []
    fly_base_x = 920
    fly_base_y = 900
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 20, 28, 255))
        draw = ImageDraw.Draw(img)
        draw_jungle_background(draw, t)
        
        mouth_pt = (360, 920)
        fly_x, fly_y = fly_base_x, fly_base_y
        
        # Frog Body & Perch
        frog_body = cubic_bezier((40, 1120), (40, 780), (180, 720), (320, 760), steps=15)
        frog_body.extend(cubic_bezier((320, 760), (400, 830), (410, 920), (360, 940), steps=15))
        frog_body.extend(cubic_bezier((360, 940), (340, 1120), (220, 1200), (60, 1180), steps=15))
        draw.polygon(frog_body, fill=(58, 148, 75), outline=(24, 68, 34), width=8)
        
        # Frog Eye
        draw.ellipse([210, 710, 290, 790], fill=(250, 195, 35), outline=(25, 20, 10), width=6)
        draw.ellipse([235, 735, 265, 765], fill=(15, 10, 5))
        draw.ellipse([225, 725, 240, 740], fill=(255, 255, 255))
        
        # Twig on Right with Green Leaves
        draw.line([(fly_base_x - 140, fly_base_y + 110), (WIDTH, fly_base_y + 140)], fill=(105, 78, 52), width=26)
        leaf_pts = cubic_bezier((fly_base_x - 90, fly_base_y + 110), (fly_base_x - 10, fly_base_y + 50),
                                (fly_base_x + 90, fly_base_y + 70), (fly_base_x + 130, fly_base_y + 120), steps=15)
        leaf_pts.extend(cubic_bezier((fly_base_x + 130, fly_base_y + 120), (fly_base_x + 50, fly_base_y + 160),
                                     (fly_base_x - 40, fly_base_y + 150), (fly_base_x - 90, fly_base_y + 110), steps=15))
        draw.polygon(leaf_pts, fill=(62, 145, 68), outline=(28, 70, 32), width=4)
        
        # Launch & Retraction Kinematics
        if t < 0.20:
            tongue_tip = mouth_pt
        elif t < 0.42:
            launch_t = ease_out_quad((t - 0.20) / 0.22)
            tongue_tip = lerp_pt(mouth_pt, (fly_base_x - 30, fly_base_y), launch_t)
        elif t < 0.65:
            tongue_tip = (fly_base_x - 10, fly_base_y)
        else:
            retract_t = ease_in_quad((t - 0.65) / 0.35)
            tongue_tip = lerp_pt((fly_base_x - 10, fly_base_y), mouth_pt, retract_t)
            fly_x = tongue_tip[0] + 25
            fly_y = tongue_tip[1]
            
        # Tongue Whip Ribbon
        if tongue_tip != mouth_pt:
            draw.line([mouth_pt, tongue_tip], fill=(238, 72, 102), width=40)
            draw.line([mouth_pt, tongue_tip], fill=(255, 145, 168), width=18)
            # Inverted mushroom suction pad
            draw.ellipse([tongue_tip[0] - 35, tongue_tip[1] - 45, tongue_tip[0] + 45, tongue_tip[1] + 45],
                         fill=(255, 115, 148), outline=(180, 28, 58), width=6)
                         
        # Insect Prey (Blowfly with animated wings)
        draw.ellipse([fly_x - 26, fly_y - 18, fly_x + 26, fly_y + 18], fill=(38, 42, 50), outline=(12, 14, 18), width=3)
        draw.ellipse([fly_x - 24, fly_y - 14, fly_x - 12, fly_y], fill=(215, 45, 45)) # Red eye
        if t < 0.42:
            w_flap = math.sin(fi * 2.2) * 18
            w_top = min(fly_y - 32 + w_flap, fly_y - 10)
            w_bot = max(fly_y - 32 + w_flap, fly_y - 6)
            draw.ellipse([fly_x - 16, int(w_top), fly_x + 14, int(w_bot)], fill=(210, 235, 255, 190))
            
        # Supersonic Shockwave & Viscoelastic Saliva Bridges
        if 0.40 <= t <= 0.68:
            shock_r = int((t - 0.40) * 550)
            draw.ellipse([fly_base_x - shock_r, fly_base_y - shock_r, fly_base_x + shock_r, fly_base_y + shock_r],
                         outline=(255, 235, 100, max(0, 255 - shock_r * 2)), width=6)
            for dy in [-20, 0, 20]:
                draw.line([(tongue_tip[0] + 18, tongue_tip[1] + dy), (fly_x, fly_y + dy)], fill=(245, 245, 190), width=8)
                
        draw_hud(draw, 540, 320, "50-G CATAPULT STRIKE & RECOIL", "Releases in 7ms — mushroom pad inverts upon impact", color=(255, 80, 100))
        if t < 0.42:
            draw_hud(draw, 540, 1600, "ELASTIC SPRING RELEASE: 50G ACCELERATION", color=(255, 215, 0))
        else:
            draw_hud(draw, 540, 1600, "SHEAR-THINNING SALIVA: INSTANT SOLID ADHESION", color=(100, 240, 255))
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "frog_tongue_slingshot_impact_adhesion.mp4")


# ==============================================================================
# 3 & 4: SEA OTTER PELT & THERMAL DRYSUIT ANIMATIONS
# ==============================================================================
def render_otter_fur_density(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (16, 26, 40, 255))
        draw = ImageDraw.Draw(img)
        draw_ocean_background(draw, t)
        
        # Skin Layer at Bottom (Hypodermis, Dermis & Epidermis)
        draw.rectangle([0, 1400, WIDTH, HEIGHT], fill=(235, 160, 150), outline=(180, 100, 90), width=6)
        # Capillary blood vessels in dermis
        for vx in range(80, WIDTH, 160):
            draw.line([(vx, 1450), (vx + 30, 1420), (vx + 60, 1440)], fill=(215, 60, 60), width=4)
        draw.text((WIDTH//2 - 160, 1470), "EPIDERMIS SKIN LAYER", font=get_font(32, bold=True), fill=(140, 60, 50))
        
        # Dense Underfur Shafts
        hair_count = 38
        interlock_t = ease_in_out(clamp((t - 0.30) / 0.50))
        
        for i in range(hair_count):
            hx = int(50 + i * (WIDTH - 100) / (hair_count - 1))
            wave = math.sin(fi * 0.15 + i * 0.35) * 14
            top_x = hx + int(wave + (30 if i % 2 == 0 else -30) * interlock_t)
            top_y = 660 + (i % 3) * 35
            
            draw.line([(hx, 1400), (top_x, top_y)], fill=(110, 75, 45), width=10)
            draw.line([(hx, 1400), (top_x, top_y)], fill=(175, 130, 90), width=4)
            
            # Microscopic Interlocking Barbs
            if interlock_t > 0.1:
                barb_alpha = int(interlock_t * 255)
                for by in range(top_y + 80, 1320, 70):
                    bx = int(lerp(hx, top_x, (1400 - by) / (1400 - top_y)))
                    draw.line([(bx, by), (bx + 20, by - 16)], fill=(220, 180, 135, barb_alpha), width=4)
                    draw.line([(bx, by), (bx - 20, by - 16)], fill=(220, 180, 135, barb_alpha), width=4)
                    
        # Magnifying Inspection Lens Inset
        zoom_cx, zoom_cy = 540, 480
        draw.ellipse([zoom_cx - 245, zoom_cy - 245, zoom_cx + 245, zoom_cy + 245],
                     fill=(24, 38, 55, 245), outline=(255, 215, 80), width=8)
        # Zipper interlocking action inside lens
        z_t = ease_in_out(clamp((t - 0.35) / 0.50))
        d_hook = lerp(80, 0, z_t)
        # Left barbed fiber
        draw.line([(zoom_cx - 100 + int(d_hook), zoom_cy - 80), (zoom_cx - 20, zoom_cy)], fill=(225, 175, 125), width=18)
        draw.line([(zoom_cx - 20, zoom_cy), (zoom_cx - 70, zoom_cy + 40)], fill=(225, 175, 125), width=18)
        # Right barbed fiber
        draw.line([(zoom_cx + 100 - int(d_hook), zoom_cy + 80), (zoom_cx + 20, zoom_cy)], fill=(185, 135, 95), width=18)
        draw.line([(zoom_cx + 20, zoom_cy), (zoom_cx + 70, zoom_cy - 40)], fill=(185, 135, 95), width=18)
        
        density_num = int(lerp(100000, 1000000, ease_out_quad(min(1.0, t * 1.6))))
        draw_hud(draw, 540, 200, "MICROSCOPIC INTERLOCKING BARBS", "Barbed underfur fibers mechanically zip into an airtight shield", color=(100, 230, 255))
        draw_hud(draw, 540, 1580, f"FUR DENSITY: {density_num:,} HAIRS / IN²",
                 "Densest pelt in the entire animal kingdom", color=(255, 215, 0))
                 
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "otter_fur_density_interlocking_barbs.mp4")

def render_otter_air_bubble_barrier(num_frames=270):
    frames = []
    np.random.seed(42)
    bubbles = [{"x": np.random.randint(120, 960), "y": np.random.randint(920, 1300), "r": np.random.randint(14, 32), "drift": np.random.uniform(0.5, 2.0)} for _ in range(55)]
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (12, 28, 48, 255))
        draw = ImageDraw.Draw(img)
        draw_ocean_background(draw, t)
        
        # Upper Freezing Arctic Ocean Water
        water_press_y = int(lerp(480, 840, ease_in_out(clamp((t - 0.25) / 0.50))))
        draw.rectangle([0, 0, WIDTH, water_press_y], fill=(20, 58, 98, 255))
        
        # Ice crystals in water
        for ix in range(80, WIDTH - 80, 120):
            iy = (ix * 3 + fi * 4) % (water_press_y - 40)
            draw.polygon([(ix, iy - 16), (ix + 14, iy), (ix, iy + 16), (ix - 14, iy)], fill=(185, 235, 255, 170))
            
        # Dense Interlocked Fur Coat
        draw.rectangle([0, water_press_y, WIDTH, 1420], fill=(78, 52, 38, 255))
        for h in range(44):
            hx = h * 25
            draw.line([(hx, 1420), (hx + int(math.sin(fi * 0.1 + h) * 10), water_press_y)], fill=(135, 95, 65), width=6)
            
        # Trapped Silvery Air Bubbles Cushion
        for b in bubbles:
            by = int(b["y"] + math.sin(fi * 0.12 + b["drift"]) * 8)
            bx = int(b["x"] + math.cos(fi * 0.09 + b["drift"]) * 6)
            if by > water_press_y + 15 and by < 1400:
                draw.ellipse([bx - b["r"], by - b["r"], bx + b["r"], by + b["r"]],
                             fill=(215, 245, 255, 200), outline=(255, 255, 255, 245), width=3)
                draw.ellipse([bx - b["r"]//2, by - b["r"]//2, bx - b["r"]//4, by - b["r"]//4], fill=(255, 255, 255, 255))
                
        # Lower Pink Skin Layer (Warm & 100% Dry)
        draw.rectangle([0, 1420, WIDTH, HEIGHT], fill=(240, 168, 155))
        draw.text((WIDTH//2 - 140, 1470), "WARM SKIN: 37°C", font=get_font(34, bold=True), fill=(160, 50, 40))
        draw.text((WIDTH//2 - 110, 1520), "100% DRY", font=get_font(28, bold=True), fill=(30, 145, 50))
        
        # Deflection boundary sheen
        draw.line([(0, water_press_y), (WIDTH, water_press_y)], fill=(120, 220, 255), width=8)
        
        draw_hud(draw, 540, 320, "FREEZING ARCTIC WATER: 0°C", "Repelled by surface tension of captive bubble layer", color=(120, 225, 255))
        draw_hud(draw, 540, 1680, "CAPTIVE AIR BUBBLE THERMAL DRYSUIT", "Zero body blubber needed — skin never gets wet", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "otter_air_bubble_thermal_barrier.mp4")


# ==============================================================================
# 5 & 6: TRAP-JAW ANT SPRING MANDIBLES ANIMATIONS
# ==============================================================================
def draw_forest_floor_background(draw, t=0.0):
    for y in range(0, HEIGHT, 16):
        ty = y / HEIGHT
        r = int(lerp(22, 38, ty))
        g = int(lerp(18, 28, ty))
        b = int(lerp(16, 22, ty))
        draw.rectangle([0, y, WIDTH, y + 16], fill=(r, g, b, 255))
        
    # Fallen leaves & soil textures
    draw.ellipse([80, 400, 280, 540], fill=(75, 48, 28), outline=(45, 28, 15), width=3)
    draw.ellipse([WIDTH - 300, 600, WIDTH - 80, 760], fill=(85, 52, 32), outline=(50, 30, 18), width=3)
    draw.ellipse([140, HEIGHT - 600, 340, HEIGHT - 460], fill=(68, 42, 24), outline=(40, 24, 12), width=3)

def render_ant_muscle_latch(num_frames=255):
    frames = []
    cx, cy = 540, 1100
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (18, 16, 22, 255))
        draw = ImageDraw.Draw(img)
        draw_forest_floor_background(draw, t)
        
        # Complete Ant Body (Thorax & Legs in background)
        draw.polygon([(cx - 70, cy + 240), (cx + 70, cy + 240), (cx + 50, cy + 420), (cx - 50, cy + 420)], fill=(42, 30, 26))
        # Articulated legs
        for leg_side in [-1, 1]:
            draw.line([(cx + 60 * leg_side, cy + 280), (cx + 260 * leg_side, cy + 240), (cx + 340 * leg_side, cy + 380)], fill=(75, 52, 42), width=8)
            draw.line([(cx + 60 * leg_side, cy + 340), (cx + 280 * leg_side, cy + 360), (cx + 360 * leg_side, cy + 500)], fill=(75, 52, 42), width=8)
            
        # Head Capsule Dorsal Anatomy
        head_pts = cubic_bezier((cx - 280, cy - 140), (cx - 330, cy + 60), (cx - 300, cy + 240), (cx, cy + 260), steps=20)
        head_pts.extend(cubic_bezier((cx, cy + 260), (cx + 300, cy + 240), (cx + 330, cy + 60), (cx + 280, cy - 140), steps=20))
        head_pts.extend(cubic_bezier((cx + 280, cy - 140), (cx + 180, cy - 180), (cx - 180, cy - 180), (cx - 280, cy - 140), steps=20))
        draw.polygon(head_pts, fill=(58, 42, 38), outline=(135, 95, 75), width=8)
        
        # Compound Eyes on Margins
        draw.ellipse([cx - 330, cy + 20, cx - 270, cy + 120], fill=(22, 18, 24), outline=(150, 100, 80), width=4)
        draw.ellipse([cx + 270, cy + 20, cx + 330, cy + 120], fill=(22, 18, 24), outline=(150, 100, 80), width=4)
        
        # Mandible Spread: 35° -> 90° (each side), total spread 70° -> 180° flat
        open_t = ease_in_out(clamp((t - 0.20) / 0.60))
        angle_deg = lerp(35, 90, open_t)
        rad = math.radians(angle_deg)
        
        m_len = 410
        lm_base = (cx - 140, cy - 160)
        rm_base = (cx + 140, cy - 160)
        lm_tip = (int(lm_base[0] - m_len * math.sin(rad)), int(lm_base[1] - m_len * math.cos(rad)))
        rm_tip = (int(rm_base[0] + m_len * math.sin(rad)), int(rm_base[1] - m_len * math.cos(rad)))
        
        # Curved Mandibles with Serrated Teeth
        draw.line([lm_base, lm_tip], fill=(165, 80, 50), width=32)
        draw.line([rm_base, rm_tip], fill=(165, 80, 50), width=32)
        draw.line([lm_base, lm_tip], fill=(235, 140, 90), width=14)
        draw.line([rm_base, rm_tip], fill=(235, 140, 90), width=14)
        
        # Closer Muscle Swelling & Striations
        m_thick = int(lerp(48, 120, open_t))
        draw.ellipse([cx - 240, cy - 80, cx - 30, cy - 80 + m_thick * 2], fill=(210, 48, 70), outline=(130, 22, 35), width=6)
        draw.ellipse([cx + 30, cy - 80, cx + 240, cy - 80 + m_thick * 2], fill=(210, 48, 70), outline=(130, 22, 35), width=6)
        for s in range(5):
            sy = cy - 60 + s * int(m_thick * 0.35)
            draw.line([(cx - 210, sy), (cx - 60, sy)], fill=(255, 110, 130), width=4)
            draw.line([(cx + 60, sy), (cx + 210, sy)], fill=(255, 110, 130), width=4)
            
        # Latch Mechanism (Engages gold when 180° reached)
        latch_color = (255, 215, 0) if open_t > 0.9 else (180, 180, 180)
        draw.rectangle([cx - 40, cy - 190, cx + 40, cy - 100], fill=latch_color, outline=(40, 40, 40), width=5)
        
        # Trigger Hairs
        draw.line([(cx - 40, cy - 180), (cx - 75, cy - 360)], fill=(245, 245, 245), width=5)
        draw.line([(cx + 40, cy - 180), (cx + 75, cy - 360)], fill=(245, 245, 245), width=5)
        
        draw_hud(draw, 540, 340, "MASSIVE CLOSER MUSCLES WINCH SPRING", "Contraction locks mandibles flat at 180 degrees", color=(255, 100, 120))
        draw_hud(draw, 540, 1550, f"MANDIBLE SPREAD: {int(angle_deg*2):03d}°",
                 "Spring latch engages when fully cocked" if open_t < 0.9 else "🔒 LATCH LOCKED (READY TO STRIKE)",
                 color=(255, 215, 0) if open_t > 0.9 else (200, 225, 255))
                 
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "trap_jaw_ant_muscle_latch_mechanism.mp4")

def render_ant_explosive_strike(num_frames=285):
    frames = []
    cx, cy = 540, 1100
    prey_y = 680
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (18, 16, 22, 255))
        draw = ImageDraw.Draw(img)
        draw_forest_floor_background(draw, t)
        
        # Airborne Recoil Somersault Jump
        recoil_y = 0
        rot_recoil = 0.0
        if t >= 0.68:
            jump_t = (t - 0.68) / 0.32
            recoil_y = int(-math.sin(jump_t * math.pi) * 520)
            rot_recoil = jump_t * math.pi * 2.0
            
        cur_cy = cy + recoil_y
        
        # Mandible Snap
        if t < 0.30:
            angle_deg = 90
        elif t < 0.36:
            snap_t = ease_in_quad((t - 0.30) / 0.06)
            angle_deg = lerp(90, 8, snap_t)
        else:
            angle_deg = 8
            
        rad = math.radians(angle_deg)
        m_len = 410
        lm_base = (cx - 140, cur_cy - 160)
        rm_base = (cx + 140, cur_cy - 160)
        lm_tip = (int(lm_base[0] - m_len * math.sin(rad)), int(lm_base[1] - m_len * math.cos(rad)))
        rm_tip = (int(rm_base[0] + m_len * math.sin(rad)), int(rm_base[1] - m_len * math.cos(rad)))
        
        # Ant Head Capsule
        head_pts = cubic_bezier((cx - 280, cur_cy - 140), (cx - 330, cur_cy + 60), (cx - 300, cur_cy + 240), (cx, cur_cy + 260), steps=15)
        head_pts.extend(cubic_bezier((cx, cur_cy + 260), (cx + 300, cur_cy + 240), (cx + 330, cur_cy + 60), (cx + 280, cur_cy - 140), steps=15))
        head_pts.extend(cubic_bezier((cx + 280, cur_cy - 140), (cx + 180, cur_cy - 180), (cx - 180, cur_cy - 180), (cx - 280, cur_cy - 140), steps=15))
        draw.polygon(head_pts, fill=(58, 42, 38), outline=(135, 95, 75), width=8)
        
        draw.line([lm_base, lm_tip], fill=(235, 140, 90), width=28)
        draw.line([rm_base, rm_tip], fill=(235, 140, 90), width=28)
        
        # Motion Blur Trails
        if 0.30 <= t <= 0.37:
            for ghost in np.linspace(0.1, 0.9, 5):
                g_ang = math.radians(lerp(90, 8, ghost))
                g_tip_l = (int(lm_base[0] - m_len * math.sin(g_ang)), int(lm_base[1] - m_len * math.cos(g_ang)))
                g_tip_r = (int(rm_base[0] + m_len * math.sin(g_ang)), int(rm_base[1] - m_len * math.cos(g_ang)))
                draw.line([lm_base, g_tip_l], fill=(255, 200, 100, 80), width=14)
                draw.line([rm_base, g_tip_r], fill=(255, 200, 100, 80), width=14)
                
        # Prey Insect
        if t < 0.35:
            draw.ellipse([cx - 44, prey_y - 32, cx + 44, prey_y + 32], fill=(95, 150, 75), outline=(48, 85, 38), width=4)
            draw.ellipse([cx - 40, prey_y - 20, cx - 20, prey_y], fill=(220, 50, 45))
        else:
            split_d = int((t - 0.35) * 700)
            draw.ellipse([cx - 70 - split_d, prey_y - 32, cx - split_d, prey_y + 32], fill=(95, 150, 75))
            draw.ellipse([cx + split_d, prey_y - 32, cx + 70 + split_d, prey_y + 32], fill=(95, 150, 75))
            
        # Supersonic Shockwave
        if 0.33 <= t <= 0.65:
            sw_r = int((t - 0.33) * 1150)
            draw.ellipse([cx - sw_r, prey_y - sw_r//2, cx + sw_r, prey_y + sw_r//2],
                         outline=(255, 235, 110, max(0, 255 - sw_r // 3)), width=8)
            for sp in range(8):
                sx = cx + int(math.cos(sp * 0.8) * sw_r * 0.75)
                sy = prey_y + int(math.sin(sp * 0.8) * sw_r * 0.45)
                draw.line([(cx, prey_y), (sx, sy)], fill=(255, 255, 215), width=4)
                
        draw_hud(draw, 540, 340, "140 MPH SUPERSONIC STRIKE", "Snaps shut in 0.1ms — 2,300x faster than an eye blink", color=(255, 80, 80))
        if t < 0.68:
            draw_hud(draw, 540, 1550, "TRIGGER HAIR TOUCH -> EXPLOSIVE ELASTIC RELEASE", color=(255, 215, 0))
        else:
            draw_hud(draw, 540, 1550, "GROUND REACTION: ESCAPE LAUNCH 40CM AIRBORNE", color=(100, 235, 255))
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "trap_jaw_ant_explosive_mandible_strike.mp4")


# ==============================================================================
# 7 & 8: PIT VIPER THERMAL PIT & CAMERA OBSCURA ANIMATIONS
# ==============================================================================
def draw_night_jungle_background(draw, t=0.0):
    for y in range(0, HEIGHT, 16):
        ty = y / HEIGHT
        r = int(lerp(8, 14, ty))
        g = int(lerp(12, 20, ty))
        b = int(lerp(24, 34, ty))
        draw.rectangle([0, y, WIDTH, y + 16], fill=(r, g, b, 255))
        
    # Crescent moon & stars
    draw.ellipse([WIDTH - 240, 140, WIDTH - 120, 260], fill=(245, 245, 220))
    draw.ellipse([WIDTH - 220, 130, WIDTH - 100, 250], fill=(10, 14, 26))
    
    # Fireflies glowing
    for fl in range(6):
        fx = int(120 + fl * 160 + math.sin(t * 3.0 + fl) * 30)
        fy = int(450 + (fl % 3) * 180 + math.cos(t * 2.5 + fl) * 25)
        draw.ellipse([fx - 8, fy - 8, fx + 8, fy + 8], fill=(225, 255, 120, 180))
        draw.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=(255, 255, 240))

def render_viper_loreal_pit(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 18, 24, 255))
        draw = ImageDraw.Draw(img)
        draw_night_jungle_background(draw, t)
        
        # Viper Coiled on Branch
        draw.line([(0, 1020), (WIDTH, 1100)], fill=(75, 52, 38), width=50)
        
        # Viper Head Profile (Smooth curved triangular viper skull)
        v_pts = cubic_bezier((140, 950), (140, 640), (450, 560), (740, 680), steps=20)
        v_pts.extend(cubic_bezier((740, 680), (880, 750), (960, 880), (880, 980), steps=20))
        v_pts.extend(cubic_bezier((880, 980), (780, 1060), (400, 1100), (140, 950), steps=20))
        draw.polygon(v_pts, fill=(52, 105, 62), outline=(26, 62, 34), width=8)
        
        # Eyeball with Vertical Cat Slit Pupil
        eye_cx, eye_cy = 740, 720
        draw.ellipse([eye_cx - 55, eye_cy - 55, eye_cx + 55, eye_cy + 55], fill=(235, 185, 38), outline=(32, 22, 12), width=6)
        draw.ellipse([eye_cx - 10, eye_cy - 48, eye_cx + 10, eye_cy + 48], fill=(12, 8, 8))
        draw.ellipse([eye_cx - 24, eye_cy - 28, eye_cx - 10, eye_cy - 14], fill=(255, 255, 255))
        
        # Loreal Pit Aperture (Between eye and nostril)
        pit_x, pit_y = 850, 830
        draw.ellipse([pit_x - 34, pit_y - 28, pit_x + 34, pit_y + 28], fill=(20, 24, 24), outline=(165, 215, 95), width=5)
        
        # Zoomed Cross-Section Lens Chamber at Center
        cx, cy = 540, 1220
        draw.ellipse([cx - 320, cy - 220, cx + 320, cy + 220], fill=(26, 34, 42), outline=(255, 215, 0), width=6)
        draw.chord([cx - 280, cy - 180, cx + 280, cy + 180], start=90, end=270, fill=(38, 48, 58))
        draw.chord([cx - 280, cy - 180, cx + 280, cy + 180], start=270, end=90, fill=(16, 22, 28))
        
        # Suspended 15μm Membrane Vibrating
        vib = math.sin(fi * 0.4) * 6
        draw.line([(cx + int(vib), cy - 170), (cx + int(vib), cy + 170)], fill=(255, 105, 125), width=8)
        for my in range(cy - 140, cy + 150, 35):
            draw.ellipse([cx - 8 + int(vib), my - 8, cx + 8 + int(vib), my + 8], fill=(255, 235, 85))
            
        draw_hud(draw, 540, 340, "LOREAL FACIAL PIT CAVITY", "Stereoscopic thermal sensory chambers between eye and nostril", color=(100, 240, 255))
        draw_hud(draw, 540, 1540, "15-MICROMETER SUSPENDED MEMBRANE", "Packed with TRPA1 infrared-sensitive ion channel receptors", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "pit_viper_loreal_pit_anatomy.mp4")

def render_viper_pinhole_thermal(num_frames=270):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (10, 12, 18, 255))
        draw = ImageDraw.Draw(img)
        draw_night_jungle_background(draw, t)
        
        mouse_x = 220
        mouse_y = int(850 + math.sin(fi * 0.08) * 20)
        
        # Warm-Blooded Mouse Silhouette & Heat Radiance
        draw.ellipse([mouse_x - 90, mouse_y - 50, mouse_x + 90, mouse_y + 50], fill=(255, 65, 25))
        draw.ellipse([mouse_x + 50, mouse_y - 45, mouse_x + 110, mouse_y + 5], fill=(255, 165, 35))
        draw.ellipse([mouse_x + 70, mouse_y - 20, mouse_x + 90, mouse_y], fill=(255, 245, 85))
        draw.line([(mouse_x - 90, mouse_y), (mouse_x - 160, mouse_y + 40)], fill=(205, 45, 25), width=6)
        
        # Radiating Infrared Waves
        for w in range(4):
            wr = int((fi * 8 + w * 120) % 500)
            draw.arc([mouse_x - wr, mouse_y - wr, mouse_x + wr, mouse_y + wr],
                     start=-45, end=45, fill=(255, 85, 25, max(0, 200 - wr // 2)), width=5)
                     
        pinhole_x, pinhole_y = 650, 850
        membrane_x = 880
        
        # Pinhole Camera Aperture Wall
        draw.rectangle([pinhole_x, 500, pinhole_x + 40, pinhole_y - 40], fill=(85, 115, 80))
        draw.rectangle([pinhole_x, pinhole_y + 40, pinhole_x + 40, 1200], fill=(85, 115, 80))
        draw.line([(membrane_x, 600), (membrane_x, 1100)], fill=(125, 165, 205), width=10)
        
        # Camera Obscura Rays
        draw.line([(mouse_x + 70, mouse_y - 40), (pinhole_x + 20, pinhole_y), (membrane_x, 1020)],
                  fill=(255, 225, 85, 225), width=4)
        draw.line([(mouse_x + 70, mouse_y + 40), (pinhole_x + 20, pinhole_y), (membrane_x, 680)],
                  fill=(255, 75, 35, 225), width=4)
                  
        # Inverted Thermal Projection Map
        draw.ellipse([membrane_x - 22, 790, membrane_x + 22, 910], fill=(255, 125, 35))
        draw.ellipse([membrane_x - 16, 730, membrane_x + 16, 795], fill=(255, 235, 65))
        
        draw_hud(draw, 540, 340, "PINHOLE CAMERA OBSCURA EFFECT", "Narrow pit aperture optically refracts infrared rays", color=(255, 165, 45))
        draw_hud(draw, 540, 1540, "INVERTED THERMAL HEATMAP PROJECTION", "Trigeminal nerve superimposes heat map over vision", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "pit_viper_pinhole_thermal_projection.mp4")


# ==============================================================================
# 9 & 10: ARCHERFISH RIFLE BARREL & WATER BULLET ANIMATIONS
# ==============================================================================
def draw_mangrove_background(draw, t=0.0):
    for y in range(0, HEIGHT, 16):
        ty = y / HEIGHT
        if y < 700:
            draw.rectangle([0, y, WIDTH, y + 16], fill=(16, 26, 36, 255))
        else:
            draw.rectangle([0, y, WIDTH, y + 16], fill=(20, 52, 85, 255))
    # Water surface sheen
    draw.line([(0, 700), (WIDTH, 700)], fill=(125, 225, 255), width=6)
    # Mangrove prop roots underwater
    for r_idx in range(4):
        rx = 120 + r_idx * 240
        draw.line([(rx, 700), (rx + 40, HEIGHT)], fill=(65, 48, 32), width=24)

def render_archerfish_palate_tongue(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (14, 30, 50, 255))
        draw = ImageDraw.Draw(img)
        draw_mangrove_background(draw, t)
        
        cx, cy = 450, 1050
        # Archerfish Body (Silver-olive with dark camouflage bands)
        fish_pts = cubic_bezier((cx - 280, cy + 180), (cx - 100, cy - 80), (cx + 100, cy - 140), (cx + 320, cy - 80), steps=15)
        fish_pts.extend(cubic_bezier((cx + 320, cy - 80), (cx + 300, cy + 180), (cx + 180, cy + 280), (cx - 280, cy + 180), steps=15))
        draw.polygon(fish_pts, fill=(190, 205, 170), outline=(42, 54, 38), width=8)
        
        # Dark vertical bands
        draw.line([(cx - 80, cy - 40), (cx - 20, cy + 220)], fill=(32, 38, 28), width=32)
        draw.line([(cx + 60, cy - 90), (cx + 110, cy + 150)], fill=(32, 38, 28), width=28)
        
        # Large Golden Targeting Eye near snout
        draw.ellipse([cx + 90, cy - 120, cx + 180, cy - 30], fill=(250, 220, 45), outline=(22, 22, 12), width=5)
        draw.ellipse([cx + 120, cy - 100, cx + 160, cy - 60], fill=(10, 10, 10))
        draw.ellipse([cx + 110, cy - 110, cx + 125, cy - 95], fill=(255, 255, 255))
        
        # Palate & Grooved Tongue Rifle Tube
        press_t = ease_in_out(clamp((t - 0.25) / 0.50))
        tongue_y = int(lerp(cy + 60, cy + 5, press_t))
        palate_y = cy
        
        draw.line([(cx + 180, palate_y - 20), (cx + 310, palate_y - 65)], fill=(225, 125, 135), width=16)
        draw.line([(cx + 180, tongue_y + 10), (cx + 300, tongue_y - 35)], fill=(245, 165, 165), width=18)
        
        if press_t > 0.4:
            draw.line([(cx + 190, cy - 5), (cx + 305, cy - 50)], fill=(105, 235, 255), width=10)
            
        gill_squeeze = int(lerp(0, 35, press_t))
        draw.arc([cx - 140 + gill_squeeze, cy + 20, cx - 40, cy + 180], start=90, end=270, fill=(245, 85, 85), width=8)
        
        draw_hud(draw, 540, 340, "GROOVED TONGUE + ROOF PALATE", "Press together to seal a rigid cylindrical rifle barrel", color=(255, 215, 0))
        draw_hud(draw, 540, 1550, "HYDRAULIC GILL PISTON COMPRESSION", "Gill covers squeeze shut to pressurize the water chamber", color=(100, 230, 255))
        
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
        draw_mangrove_background(draw, t)
        
        draw.rectangle([0, 1400, WIDTH, HEIGHT], fill=(22, 62, 110, 255))
        draw.line([(0, 1400), (WIDTH, 1400)], fill=(125, 225, 255), width=5)
        
        # Overhanging Tree Branch with Leaves
        draw.line([(branch_x - 300, branch_y + 120), (WIDTH, branch_y - 50)], fill=(95, 70, 50), width=28)
        draw.ellipse([branch_x - 140, branch_y + 20, branch_x - 30, branch_y + 80], fill=(62, 145, 55))
        draw.ellipse([branch_x - 20, branch_y - 30, branch_x + 90, branch_y + 30], fill=(72, 160, 65))
        
        # Grasshopper Prey
        gh_alive = t < 0.60
        gh_x = branch_x - 80
        gh_y = branch_y + 15
        if not gh_alive:
            fall_t = (t - 0.60) / 0.40
            gh_x += int(fall_t * 60)
            gh_y += int(fall_t * fall_t * 920)
            
        draw.ellipse([gh_x - 32, gh_y - 16, gh_x + 32, gh_y + 16], fill=(85, 185, 65), outline=(32, 98, 28), width=4)
        draw.line([(gh_x + 10, gh_y), (gh_x + 35, gh_y - 25)], fill=(85, 185, 65), width=5)
        
        mouth_x, mouth_y = 260, 1380
        target = (branch_x - 90, branch_y + 15)
        
        if t < 0.20:
            bullet_pos = (mouth_x, mouth_y)
        elif t < 0.60:
            flight_t = (t - 0.20) / 0.40
            bullet_pos = lerp_pt((mouth_x, mouth_y), target, ease_out_quad(flight_t))
            draw.line([(mouth_x, mouth_y), bullet_pos], fill=(125, 215, 255, 165), width=int(lerp(6, 24, flight_t)))
            drop_r = int(lerp(14, 40, flight_t))
            draw.ellipse([bullet_pos[0] - drop_r, bullet_pos[1] - drop_r, bullet_pos[0] + drop_r, bullet_pos[1] + drop_r],
                         fill=(185, 245, 255, 240), outline=(255, 255, 255), width=4)
        else:
            bullet_pos = target
            spl_t = (t - 0.60) / 0.40
            for sp in range(14):
                ang = sp * (2 * math.pi / 14)
                sp_d = int(spl_t * 380)
                sx = target[0] + int(math.cos(ang) * sp_d)
                sy = target[1] + int(math.sin(ang) * sp_d * 0.7)
                draw.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=(185, 240, 255, max(0, 255 - sp_d)))
                
        draw_hud(draw, 540, 320, "MID-AIR WATER BULLET COALESCENCE", "Trailing water moves faster than front, bunching into a slug", color=(100, 230, 255))
        if t < 0.60:
            draw_hud(draw, 540, 1550, "VELOCITY: 5 M/S -> IMPACT MASS CONCENTRATION", color=(255, 215, 0))
        else:
            draw_hud(draw, 540, 1550, "6X KINETIC FORCE KNOCKS PREY OFF PERCH", color=(255, 100, 100))
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "archerfish_water_bullet_coalescence_strike.mp4")


# ==============================================================================
# 11 & 12: CROCODILE JAW MUSCLE BITE & DEATH ROLL ANIMATIONS
# ==============================================================================
def draw_riverbed_background(draw, t=0.0):
    for y in range(0, HEIGHT, 16):
        ty = y / HEIGHT
        r = int(lerp(14, 22, ty))
        g = int(lerp(28, 38, ty))
        b = int(lerp(24, 30, ty))
        draw.rectangle([0, y, WIDTH, y + 16], fill=(r, g, b, 255))
    # River silt particles floating
    for s_idx in range(12):
        sx = int(80 + s_idx * 80 + math.sin(t * 2.0 + s_idx) * 20)
        sy = int(300 + (s_idx * 110) % 1200)
        draw.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(180, 160, 120, 120))

def render_crocodile_jaw_muscle_bite(num_frames=255):
    frames = []
    cx, cy = 420, 950
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (20, 24, 22, 255))
        draw = ImageDraw.Draw(img)
        draw_riverbed_background(draw, t)
        
        clamp_t = ease_in_out(clamp((t - 0.25) / 0.45))
        gape_deg = lerp(40, 4, clamp_t)
        rad = math.radians(gape_deg)
        
        upper_pts = cubic_bezier((cx - 260, cy - 140), (cx - 100, cy - 180), (cx + 200, cy - 120), (cx + 440, cy - 40), steps=15)
        upper_pts.extend([(cx + 460, cy), (cx - 200, cy + 20)])
        draw.polygon(upper_pts, fill=(58, 80, 64), outline=(24, 42, 30), width=8)
        
        # Amber Eye
        draw.ellipse([cx - 50, cy - 170, cx + 20, cy - 100], fill=(240, 185, 40), outline=(20, 15, 10), width=5)
        draw.ellipse([cx - 20, cy - 160, cx - 10, cy - 110], fill=(10, 10, 10))
        
        # Lower Jaw Swinging Shut
        low_end_x = int(cx + 450 * math.cos(rad))
        low_end_y = int(cy + 450 * math.sin(rad))
        draw.line([(cx - 200, cy + 40), (low_end_x, low_end_y)], fill=(78, 100, 76), width=44)
        
        # Teeth
        for tx in range(cx - 80, cx + 420, 55):
            draw.polygon([(tx, cy), (tx + 12, cy + 30), (tx - 12, cy + 30)], fill=(245, 245, 235))
            draw.polygon([(tx + 25, low_end_y), (tx + 37, low_end_y - 30), (tx + 13, low_end_y - 30)], fill=(245, 245, 235))
            
        # Pterygoid Muscle Spindle
        m_thick = int(lerp(55, 150, clamp_t))
        draw.ellipse([cx - 220, cy - 100, cx - 10, cy - 100 + m_thick * 2], fill=(195, 42, 58), outline=(115, 20, 32), width=6)
        for s in range(5):
            sy = cy - 80 + s * int(m_thick * 0.38)
            draw.line([(cx - 200, sy), (cx - 30, sy)], fill=(255, 110, 125), width=5)
            
        if clamp_t > 0.95:
            shake = int(math.sin(fi * 2.0) * 10)
            draw.line([(cx + 400 + shake, cy - 70), (cx + 400 + shake, cy + 70)], fill=(255, 235, 85), width=8)
            draw.ellipse([cx + 380 + shake, cy - 30, cx + 440 + shake, cy + 30], fill=(255, 255, 180, 200))
            
        draw_hud(draw, 540, 340, "MASSIVE PTERYGOID CLOSER MUSCLES", "Fill the rear skull to generate 3,700 lbs crushing force", color=(255, 100, 120))
        draw_hud(draw, 540, 1550, f"BITE PRESSURE: {int(clamp_t*3700):,d} LBS/IN²",
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
        draw_riverbed_background(draw, t)
        
        spin_t = ease_in_quad(clamp((t - 0.20) / 0.60))
        angle = fi * (0.1 + spin_t * 0.7)
        
        for vr in range(120, 600, 85):
            rot_r = int((angle * 40 + vr) % 600)
            alpha = int(max(0, min(255, 180 - rot_r // 3)))
            draw.ellipse([cx - rot_r, cy - rot_r//2, cx + rot_r, cy + rot_r//2],
                         outline=(85, 185, 240, alpha), width=6)
                         
        body_w = int(250 + math.cos(angle) * 85)
        body_h = int(125 + math.sin(angle) * 65)
        draw.ellipse([cx - body_w, cy - body_h, cx + body_w, cy + body_h], fill=(48, 78, 58), outline=(22, 42, 28), width=8)
        draw.arc([cx - 360, cy - 260, cx + 360, cy + 260], start=int(math.degrees(angle)), end=int(math.degrees(angle) + 130),
                 fill=(205, 245, 255), width=12)
                 
        draw_hud(draw, 540, 340, "ROTATIONAL INERTIA REDUCTION", "Tucks limbs against torso to spin like a high-speed drill", color=(100, 230, 255))
        draw_hud(draw, 540, 1550, f"DEATH ROLL ROTATION: {int(spin_t*300):03d} RPM",
                 "Rotational shear torque tears meat along anatomical fault lines", color=(255, 215, 0))
                 
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "crocodile_death_roll_rotational_inertia.mp4")


# ==============================================================================
# 13 & 14: ELECTRIC EEL ELECTROCYTE COLUMNS & LIGHTNING DISCHARGE
# ==============================================================================
def draw_amazon_river_background(draw, t=0.0):
    for y in range(0, HEIGHT, 16):
        ty = y / HEIGHT
        r = int(lerp(8, 16, ty))
        g = int(lerp(18, 30, ty))
        b = int(lerp(28, 42, ty))
        draw.rectangle([0, y, WIDTH, y + 16], fill=(r, g, b, 255))

def render_eel_electrocyte_stacks(num_frames=255):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (12, 24, 38, 255))
        draw = ImageDraw.Draw(img)
        draw_amazon_river_background(draw, t)
        
        # Complete Eel Body Profile
        draw.rounded_rectangle([160, 480, WIDTH - 160, 1420], radius=90, fill=(28, 48, 64), outline=(65, 105, 135), width=8)
        
        # Head area labeled
        draw.text((220, 520), "VITAL ORGANS (20%)", font=get_font(26, bold=True), fill=(160, 200, 230))
        draw.text((WIDTH - 420, 520), "ELECTRIC ORGANS (80%)", font=get_font(26, bold=True), fill=(255, 215, 50))
        
        # 5 Columns of 22 Disc Electrocytes Stacked in Series (like coins)
        cols = 5
        discs_per_col = 22
        for c in range(cols):
            col_x = 260 + c * 135
            for d in range(discs_per_col):
                col_y = 580 + d * 36
                draw.ellipse([col_x - 45, col_y - 12, col_x + 45, col_y + 12],
                             fill=(65, 115, 150), outline=(125, 205, 245), width=2)
                             
        # Cellular Zoom Inset
        zoom_cx, zoom_cy = 540, 1260
        draw.ellipse([zoom_cx - 260, zoom_cy - 120, zoom_cx + 260, zoom_cy + 120],
                     fill=(22, 38, 54), outline=(255, 215, 0), width=6)
        draw.text((zoom_cx - 180, zoom_cy - 20), "INACTIVE (-)", font=get_font(28, bold=True), fill=(145, 185, 225))
        draw.text((zoom_cx + 50, zoom_cy - 20), "SODIUM Na+", font=get_font(28, bold=True), fill=(255, 205, 65))
        
        draw_hud(draw, 540, 320, "6,000 ELECTROCYTES IN SERIES", "Occupies over 80% of the entire body volume", color=(100, 230, 255))
        draw_hud(draw, 540, 1550, "STACKED LIKE ROLLS OF COINS", "Each disc cell produces 0.15 volts at rest", color=(255, 215, 0))
        
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "electric_eel_electrocyte_stack_columns.mp4")

def render_eel_lightning_discharge(num_frames=285):
    frames = []
    np.random.seed(42)
    for fi in range(num_frames):
        t = fi / num_frames
        img_np = np.full((HEIGHT, WIDTH, 3), (12, 18, 28), dtype=np.uint8)
        
        eel_y1, eel_y2 = 450, 1350
        cv2.rectangle(img_np, (350, eel_y1), (730, eel_y2), (48, 68, 85), -1)
        cv2.rectangle(img_np, (350, eel_y1), (730, eel_y2), (125, 185, 225), 4)
        
        discharge_t = ease_in_quad(clamp((t - 0.20) / 0.50))
        voltage = int(discharge_t * 860)
        
        # Branching Lightning Plasma Arcs through Water
        if discharge_t > 0.35:
            num_bolts = int(lerp(3, 10, (discharge_t - 0.35) / 0.65))
            for b in range(num_bolts):
                p1 = (np.random.randint(380, 700), np.random.randint(eel_y1 + 50, eel_y2 - 50))
                p2 = (np.random.choice([np.random.randint(40, 250), np.random.randint(830, 1040)]),
                      np.random.randint(300, 1600))
                
                dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                steps = max(5, int(dist / 25))
                pts = [p1]
                dx = (p2[0] - p1[0]) / steps
                dy = (p2[1] - p1[1]) / steps
                for i in range(1, steps):
                    jx = np.random.uniform(-25, 25)
                    jy = np.random.uniform(-25, 25)
                    pts.append((int(p1[0] + dx * i + jx), int(p1[1] + dy * i + jy)))
                pts.append(p2)
                
                for i in range(len(pts) - 1):
                    cv2.line(img_np, pts[i], pts[i+1], (0, 120, 255), 14)
                for i in range(len(pts) - 1):
                    cv2.line(img_np, pts[i], pts[i+1], (0, 255, 255), 5)
                for i in range(len(pts) - 1):
                    cv2.line(img_np, pts[i], pts[i+1], (255, 255, 255), 2)
                    
        img_pil = Image.fromarray(img_np)
        draw = ImageDraw.Draw(img_pil)
        
        draw_hud(draw, 540, 320, "SERIES VOLTAGE MULTIPLICATION", "0.15V x 6,000 cells synchronizing in 1 millisecond", color=(100, 240, 255))
        draw_hud(draw, 540, 1550, f"VOLTAGE DISCHARGE: {voltage:03d} VOLTS",
                 "Enough electrical power to stun an adult horse" if voltage > 600 else "Sodium ion channels opening in series",
                 color=(255, 235, 50) if voltage > 600 else (200, 225, 255))
                 
        frames.append(cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR))
    return save_mp4(frames, "electric_eel_series_voltage_lightning_discharge.mp4")


# ==============================================================================
# BATCH EXECUTION ENTRY POINT
# ==============================================================================
def render_all():
    print("🚀 Rendering all 14 super realistic cartoon animation sequences...", flush=True)
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
    print("🎉 All 14 super realistic cartoon animations rendered successfully!", flush=True)

if __name__ == "__main__":
    render_all()



