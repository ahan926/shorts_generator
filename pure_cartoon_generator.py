"""
Pure Cartoon Animation Engine (100% Vector Animation - Zero Static Images)
Draws organic, cel-shaded scientific cartoon animations with smooth curves,
articulated joints, dynamic fluid/particle physics, and supersonic shockwaves.
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
# Smooth Geometry & Easing Helpers
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

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_pt(p1, p2, t):
    return (int(lerp(p1[0], p2[0], t)), int(lerp(p1[1], p2[1], t)))

def get_font(size=36, bold=True):
    try:
        font_path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def draw_hud(draw, x, y, title, subtitle="", color=(255, 215, 0), bg=(12, 18, 28, 235)):
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
    
    draw.rounded_rectangle([bx - 2, by - 2, bx + badge_w + 2, by + badge_h + 2], radius=18, outline=(color[0]//2, color[1]//2, color[2]//2, 120), width=4)
    draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=16, fill=bg, outline=color, width=3)
    draw.text((bx + (badge_w - w_t) // 2, by + pad_y), title, font=font_title, fill=color)
    if subtitle:
        draw.text((bx + (badge_w - w_s) // 2, by + pad_y + h_t + 8), subtitle, font=font_sub, fill=(225, 235, 245))

def draw_coiled_spring(draw, p1, p2, coils=8, radius=42, color=(255, 215, 50), width=10):
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
                  fill=(160, 120, 20), width=width + 2)
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
    print(f"✅ Generated pure animation: {filename} ({len(frames)} frames, {len(frames)/fps:.1f}s)", flush=True)
    return out_path


# ==============================================================================
# 1 & 2: FROG PURE ANIMATIONS (ZERO STATIC IMAGES)
# ==============================================================================
def render_frog_muscle_compression(num_frames=240):
    frames = []
    for fi in range(num_frames):
        t = fi / num_frames
        
        # 1. Cinematic Background Gradient
        img = Image.new("RGBA", (WIDTH, HEIGHT), (12, 18, 26, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([WIDTH//2 - 500, HEIGHT//2 - 500, WIDTH//2 + 500, HEIGHT//2 + 500], fill=(20, 32, 45, 255))
        
        # 2. Dynamic Biological Cutaway Profile
        # Mouth opens wide: hinge animation
        gape_t = ease_in_out(min(1.0, t * 2.2))
        lower_jaw_angle = lerp(0.0, 32.0, gape_t)
        jaw_rad = math.radians(lower_jaw_angle)
        
        # Frog Body & Skull Base
        # Smooth curved upper head
        head_cx, head_cy = 280, 850
        pts_upper = []
        for a in np.linspace(math.pi * 0.9, math.pi * 1.9, 30):
            rx = 340 + math.cos(a * 2) * 40
            ry = 260 + math.sin(a * 3) * 30
            pts_upper.append((int(head_cx + math.cos(a) * rx), int(head_cy + math.sin(a) * ry)))
        pts_upper.append((head_cx + 480, head_cy + 80)) # Upper snout tip
        pts_upper.append((head_cx + 120, head_cy + 80)) # Throat hinge
        
        draw.polygon(pts_upper, fill=(58, 138, 75), outline=(22, 65, 32), width=8)
        # Belly light tone
        draw.chord([head_cx - 200, head_cy - 100, head_cx + 200, head_cy + 200], start=45, end=180, fill=(185, 215, 140))
        
        # Big Cartoon Frog Eye with depth
        eye_x, eye_y = head_cx + 140, head_cy - 180
        draw.ellipse([eye_x - 70, eye_y - 70, eye_x + 70, eye_y + 70], fill=(250, 205, 40), outline=(30, 20, 10), width=7)
        draw.ellipse([eye_x - 45, eye_y - 18, eye_x + 45, eye_y + 18], fill=(15, 10, 5)) # Slit pupil
        draw.ellipse([eye_x - 30, eye_y - 45, eye_x - 10, eye_y - 25], fill=(255, 255, 255)) # Specular glint
        
        # Lower Jaw (Hinged Articulation)
        hinge_pt = (head_cx + 120, head_cy + 80)
        jaw_len = 460
        jaw_tip_x = int(hinge_pt[0] + jaw_len * math.cos(jaw_rad + 0.1))
        jaw_tip_y = int(hinge_pt[1] + jaw_len * math.sin(jaw_rad + 0.1))
        
        pts_lower = [hinge_pt, (jaw_tip_x, jaw_tip_y), (jaw_tip_x - 60, jaw_tip_y + 90), (hinge_pt[0] - 80, hinge_pt[1] + 160)]
        draw.polygon(pts_lower, fill=(72, 155, 88), outline=(22, 65, 32), width=8)
        
        # Oral Cavity Interior
        pts_oral = [hinge_pt, (head_cx + 470, head_cy + 80), (jaw_tip_x, jaw_tip_y)]
        draw.polygon(pts_oral, fill=(155, 45, 65), outline=(75, 18, 28), width=6)
        
        # Hyoglossus Contractor Muscle Bundle (Visibly Swelling and Contracting)
        compress_t = ease_in_out(clamp((t - 0.25) / 0.50))
        m_start = (hinge_pt[0] + 40, hinge_pt[1] + 10)
        m_len = int(lerp(340, 150, compress_t))
        m_thick = int(lerp(40, 105, compress_t))
        m_end = (m_start[0] + m_len, m_start[1])
        
        # Muscle belly
        draw.ellipse([m_start[0], m_start[1] - m_thick//2, m_end[0], m_start[1] + m_thick//2],
                     fill=(210, 42, 65), outline=(110, 18, 30), width=5)
        # Muscle fiber striations
        for s in range(6):
            sx = int(m_start[0] + m_len * (s + 1) / 7)
            draw.line([(sx, m_start[1] - m_thick//2 + 8), (sx, m_start[1] + m_thick//2 - 8)],
                      fill=(255, 110, 130), width=5)
                      
        # Collagen Spring Coils (Compressing tightly)
        spring_start = m_end
        spring_end = (jaw_tip_x - 40, jaw_tip_y - 20)
        spring_rad = int(lerp(30, 52, compress_t))
        draw_coiled_spring(draw, spring_start, spring_end, coils=7, radius=spring_rad, color=(255, 215, 50), width=10)
        
        # Mechanical Latch & Kinetic Energy Sparks
        if compress_t > 0.6:
            pulse = math.sin(fi * 0.8) * 18
            draw.ellipse([spring_end[0] - 50 - int(pulse), spring_end[1] - 50 - int(pulse),
                          spring_end[0] + 50 + int(pulse), spring_end[1] + 50 + int(pulse)],
                         outline=(255, 245, 100, 220), width=5)
            # Arrow indicating compression force
            draw.line([(m_end[0] + 60, m_start[1] - 80), (m_end[0] - 30, m_start[1] - 80)], fill=(255, 90, 90), width=7)
            draw.polygon([(m_end[0] - 40, m_start[1] - 80), (m_end[0] - 20, m_start[1] - 95), (m_end[0] - 20, m_start[1] - 65)], fill=(255, 90, 90))
            
        draw_hud(draw, 540, 320, "HYOGLOSSUS CONTRACTOR MUSCLE", "Contracts backward to winch the coiled collagen spring", color=(255, 100, 120))
        draw_hud(draw, 540, 1600, f"STORED ELASTIC POTENTIAL: {int(compress_t*50):02d}G FORCE",
                 "Mechanical catapult cocked for supersonic release", color=(255, 215, 0))
                 
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "frog_elastic_muscle_energy_storage.mp4")

def render_frog_tongue_launch(num_frames=270):
    frames = []
    fly_base_x = 900
    fly_base_y = 920
    
    for fi in range(num_frames):
        t = fi / num_frames
        img = Image.new("RGBA", (WIDTH, HEIGHT), (12, 18, 26, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([WIDTH//2 - 500, HEIGHT//2 - 500, WIDTH//2 + 500, HEIGHT//2 + 500], fill=(20, 32, 45, 255))
        
        mouth_pt = (340, 920)
        fly_x, fly_y = fly_base_x, fly_base_y
        
        # Frog on Left (Full Cartoon Body)
        frog_pts = [(40, 720), (220, 750), (340, 920), (280, 1160), (100, 1220), (30, 1060)]
        draw.polygon(frog_pts, fill=(58, 138, 75), outline=(22, 65, 32), width=8)
        draw.ellipse([160, 710, 240, 790], fill=(250, 205, 40), outline=(30, 20, 10), width=5)
        draw.ellipse([190, 735, 220, 765], fill=(15, 10, 5))
        
        # Tree Twig on Right
        draw.line([(fly_base_x - 60, fly_base_y + 80), (WIDTH, fly_base_y + 120)], fill=(110, 80, 55), width=24)
        
        # Launch & Retract Timeline
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
            fly_x = tongue_tip[0] + 20
            fly_y = tongue_tip[1]
            
        # Draw Elastic Tongue Ribbon (Muscular fleshy texture)
        if tongue_tip != mouth_pt:
            draw.line([mouth_pt, tongue_tip], fill=(235, 75, 105), width=38)
            draw.line([mouth_pt, tongue_tip], fill=(255, 145, 165), width=16)
            # Inverted mushroom pad
            draw.ellipse([tongue_tip[0] - 32, tongue_tip[1] - 42, tongue_tip[0] + 42, tongue_tip[1] + 42],
                         fill=(255, 115, 148), outline=(180, 30, 60), width=5)
                         
        # Cartoon Insect (Fly with animated wings)
        draw.ellipse([fly_x - 24, fly_y - 15, fly_x + 24, fly_y + 15], fill=(35, 38, 45), outline=(10, 10, 15), width=3)
        if t < 0.42:
            w_flap = math.sin(fi * 2.2) * 18
            w_top = min(fly_y - 30 + w_flap, fly_y - 10)
            w_bot = max(fly_y - 30 + w_flap, fly_y - 6)
            draw.ellipse([fly_x - 14, int(w_top), fly_x + 12, int(w_bot)], fill=(210, 235, 255, 190))
            
        # Impact Waves & Viscoelastic Saliva Strands
        if 0.40 <= t <= 0.68:
            shock_r = int((t - 0.40) * 550)
            draw.ellipse([fly_base_x - shock_r, fly_base_y - shock_r, fly_base_x + shock_r, fly_base_y + shock_r],
                         outline=(255, 235, 100, max(0, 255 - shock_r * 2)), width=6)
            for dy in [-18, 0, 18]:
                draw.line([(tongue_tip[0] + 15, tongue_tip[1] + dy), (fly_x, fly_y + dy)], fill=(245, 245, 190), width=7)
                
        draw_hud(draw, 540, 320, "50-G CATAPULT STRIKE & RECOIL", "Releases in 7ms — mushroom pad inverts upon impact", color=(255, 80, 100))
        if t < 0.42:
            draw_hud(draw, 540, 1600, "ELASTIC SPRING RELEASE: 50G ACCELERATION", color=(255, 215, 0))
        else:
            draw_hud(draw, 540, 1600, "SHEAR-THINNING SALIVA: INSTANT SOLID ADHESION", color=(100, 240, 255))
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        frames.append(frame)
    return save_mp4(frames, "frog_tongue_slingshot_impact_adhesion.mp4")

if __name__ == "__main__":
    render_frog_muscle_compression()
    render_frog_tongue_launch()
