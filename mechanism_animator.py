"""
Mechanism Animator: Procedural and composited scientific video animations
explaining biological, mechanical, and physical processes for YouTube Shorts.
"""
import math
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, CACHE_DIR

def get_ffmpeg_binary() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    """Safely retrieves a Windows system TrueType font or falls back to default."""
    try:
        if mono:
            font_path = "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"
        elif bold:
            font_path = "C:/Windows/Fonts/segoeuib.ttf"
        else:
            font_path = "C:/Windows/Fonts/segoeui.ttf"
            
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()

def draw_hud_bracket(draw: ImageDraw.Draw, bbox: Tuple[int, int, int, int], color: Tuple[int, int, int], arm_len: int = 24, width: int = 2):
    """Draws corner brackets around a bounding box for a high-tech scientific HUD look."""
    x1, y1, x2, y2 = bbox
    # Top-Left
    draw.line([(x1, y1), (x1 + arm_len, y1)], fill=color, width=width)
    draw.line([(x1, y1), (x1, y1 + arm_len)], fill=color, width=width)
    # Top-Right
    draw.line([(x2, y1), (x2 - arm_len, y1)], fill=color, width=width)
    draw.line([(x2, y1), (x2, y1 + arm_len)], fill=color, width=width)
    # Bottom-Left
    draw.line([(x1, y2), (x1 + arm_len, y2)], fill=color, width=width)
    draw.line([(x1, y2), (x1, y2 - arm_len)], fill=color, width=width)
    # Bottom-Right
    draw.line([(x2, y2), (x2 - arm_len, y2)], fill=color, width=width)
    draw.line([(x2, y2), (x2, y2 - arm_len)], fill=color, width=width)

def generate_trigger_hair_animation(
    output_path: Path,
    duration: float = 6.0,
    background_image_path: Optional[Path] = None
) -> Path:
    """
    Renders an animated 1080x1920 30fps explanation clip showing the
    microscopic sensory trigger hair structure, deflection, and mechanoreceptor cells.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = int(duration * VIDEO_FPS)
    
    font_title = get_font(42, bold=True)
    font_sub = get_font(24, mono=True)
    font_label = get_font(28, bold=True)
    font_small = get_font(20, mono=True)
    
    # Load background if provided
    bg_img = None
    if background_image_path and background_image_path.exists():
        try:
            raw_bg = Image.open(background_image_path).convert("RGB")
            # Scale and center crop to 1080x1920
            w_ratio = VIDEO_WIDTH / raw_bg.width
            h_ratio = VIDEO_HEIGHT / raw_bg.height
            scale = max(w_ratio, h_ratio)
            new_w, new_h = int(raw_bg.width * scale), int(raw_bg.height * scale)
            resized = raw_bg.resize((new_w, new_h), Image.Resampling.LANCZOS)
            x_off = (new_w - VIDEO_WIDTH) // 2
            y_off = (new_h - VIDEO_HEIGHT) // 2
            bg_img = resized.crop((x_off, y_off, x_off + VIDEO_WIDTH, y_off + VIDEO_HEIGHT))
            # Dim background slightly for maximum HUD contrast
            dim = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 15, 25))
            bg_img = Image.blend(bg_img, dim, 0.45)
        except Exception:
            bg_img = None

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    raw_video_path = output_path.with_suffix(".temp.mp4")
    out_video = cv2.VideoWriter(str(raw_video_path), fourcc, VIDEO_FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))
    
    for frame_idx in range(total_frames):
        t = frame_idx / VIDEO_FPS
        progress = frame_idx / total_frames
        
        # Base canvas
        if bg_img:
            frame = bg_img.copy()
        else:
            # Dark navy gradient
            frame = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (12, 18, 28))
            
        draw = ImageDraw.Draw(frame)
        
        # Subtle laboratory grid lines
        grid_step = 80
        for gx in range(0, VIDEO_WIDTH, grid_step):
            draw.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(20, 32, 48, 80), width=1)
        for gy in range(0, VIDEO_HEIGHT, grid_step):
            draw.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(20, 32, 48, 80), width=1)

        # Header HUD
        draw.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 220), outline=(30, 80, 130), width=2)
        draw_hud_bracket(draw, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), arm_len=18, width=2)
        draw.text((80, 80), "VENUS FLYTRAP SENSORY MECHANISM", fill=(255, 255, 255), font=font_title)
        draw.text((80, 140), "SYSTEM: MICROSCOPIC LEVER-ARM MECHANORECEPTOR", fill=(0, 210, 255), font=font_sub)
        
        # Main Diagram Box (Center-Top)
        diag_bbox = (50, 220, VIDEO_WIDTH - 50, 880)
        draw.rectangle(diag_bbox, fill=(12, 20, 32, 230), outline=(25, 65, 110), width=2)
        draw_hud_bracket(draw, diag_bbox, (0, 220, 255), arm_len=24, width=2)
        draw.text((80, 240), "[ANATOMICAL CROSS-SECTION]", fill=(120, 180, 240), font=font_sub)

        # Draw Leaf Base Curve
        leaf_pts = []
        for x in range(80, VIDEO_WIDTH - 80, 10):
            norm_x = (x - 80) / (VIDEO_WIDTH - 160)
            y = 760 - int(math.sin(norm_x * math.pi) * 90)
            leaf_pts.append((x, y))
        draw.line(leaf_pts, fill=(40, 160, 80), width=14)
        
        # Red digestive gland layer
        red_pts = [(x, y - 6) for x, y in leaf_pts]
        draw.line(red_pts, fill=(190, 45, 55), width=6)
        
        # Draw 3 Trigger Hairs (T1, T2, T3)
        hair_x_positions = [VIDEO_WIDTH // 2 - 240, VIDEO_WIDTH // 2, VIDEO_WIDTH // 2 + 240]
        for h_i, hx in enumerate(hair_x_positions):
            norm_x = (hx - 80) / (VIDEO_WIDTH - 160)
            hy = 760 - int(math.sin(norm_x * math.pi) * 90) - 6
            
            # Active bending on Center Hair (T2)
            if h_i == 1:
                # Mechanical bending cycle
                bend_angle = math.sin(t * 3.5) * 14 if t > 1.2 else 0.0
                rad = math.radians(bend_angle)
                tip_x = hx + int(math.sin(rad) * 220)
                tip_y = hy - int(math.cos(rad) * 220)
                
                # Hair body
                draw.line([(hx, hy), (tip_x, tip_y)], fill=(180, 255, 120), width=6)
                # Flexible podium base
                draw.ellipse([hx - 22, hy - 14, hx + 22, hy + 14], fill=(220, 160, 40), outline=(255, 220, 80), width=2)
                
                # Deflection arrow & angle indicator
                if abs(bend_angle) > 2:
                    draw.arc([hx - 120, hy - 240, hx + 120, hy], start=-90, end=-90 + int(bend_angle * 1.5), fill=(0, 240, 255), width=3)
                    draw.text((hx + 30, hy - 250), f"DEFLECTION: {abs(bend_angle):.1f}°", fill=(0, 240, 255), font=font_small)

                # Glowing receptor spark at the base
                spark_radius = int(12 + math.sin(t * 12) * 6)
                draw.ellipse([hx - spark_radius, hy - spark_radius, hx + spark_radius, hy + spark_radius], outline=(0, 255, 255), width=3)
                
                draw.text((hx - 40, hy - 270), "T2 [ACTIVE]", fill=(255, 220, 80), font=font_label)
            else:
                # Static upright hair
                draw.line([(hx, hy), (hx, hy - 180)], fill=(120, 200, 80), width=4)
                draw.ellipse([hx - 14, hy - 8, hx + 14, hy + 8], fill=(160, 120, 30), outline=(200, 160, 40), width=2)
                draw.text((hx - 20, hy - 210), f"T{h_i+1}", fill=(160, 200, 160), font=font_label)

        # Microscopic Zoom Circle (Callout)
        zoom_cx, zoom_cy, zoom_r = VIDEO_WIDTH // 2, 520, 160
        draw.ellipse([zoom_cx - zoom_r, zoom_cy - zoom_r, zoom_cx + zoom_r, zoom_cy + zoom_r], fill=(8, 14, 22), outline=(0, 210, 255), width=4)
        draw.text((zoom_cx - 130, zoom_cy - zoom_r - 35), "ZOOM: MECHANOSENSITIVE BASE", fill=(0, 210, 255), font=font_small)
        
        # Mechanosensitive Ion Channels Animation
        for ring_i in range(4):
            wave_r = int((t * 60 + ring_i * 45) % zoom_r)
            alpha_color = (0, int(255 * (1 - wave_r / zoom_r)), 255)
            draw.ellipse([zoom_cx - wave_r, zoom_cy - wave_r, zoom_cx + wave_r, zoom_cy + wave_r], outline=alpha_color, width=2)
            
        draw.text((zoom_cx - 80, zoom_cy - 10), "Ca2+ INFLUX", fill=(255, 255, 255), font=font_label)
        draw.text((zoom_cx - 105, zoom_cy + 25), "STRETCH-ACTIVATED", fill=(100, 220, 140), font=font_small)

        # Lower Telemetry Card
        card_bbox = (50, 920, VIDEO_WIDTH - 50, 1400)
        draw.rectangle(card_bbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(draw, card_bbox, (0, 220, 255), arm_len=20, width=2)
        draw.text((80, 940), "BIOPHYSICAL SENSOR TELEMETRY", fill=(120, 180, 240), font=font_sub)
        
        telemetry = [
            ("MECHANORECEPTOR CELL TYPE", "Sensory Podioid Epidermal Layer"),
            ("ACTIVATION THRESHOLD", "3.5 Micro-Joules Kinetic Work"),
            ("ION CHANNEL REACTION TIME", "14.2 Milliseconds"),
            ("TRANSMISSION VECTOR", "Plasmodesmata Symplastic Flow"),
            ("RESTING STATE VOLTAGE", "-120 mV Hyperpolarized")
        ]
        
        for row_i, (k, v) in enumerate(telemetry):
            ry = 990 + row_i * 75
            draw.text((80, ry), k, fill=(140, 160, 190), font=font_small)
            draw.text((80, ry + 28), v, fill=(240, 245, 255), font=font_label)
            draw.line([(80, ry + 62), (VIDEO_WIDTH - 80, ry + 62)], fill=(30, 50, 75), width=1)

        # Convert PIL frame to OpenCV BGR numpy array
        np_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        out_video.write(np_frame)
        
    out_video.release()
    
    # Transcode with imageio-ffmpeg for clean H.264 vertical video
    ffmpeg_exe = get_ffmpeg_binary()
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(raw_video_path.resolve()),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        str(output_path.resolve())
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    raw_video_path.unlink(missing_ok=True)
    return output_path

def generate_counting_timer_animation(
    output_path: Path,
    duration: float = 7.2
) -> Path:
    """
    Renders an animated 1080x1920 30fps explanation clip showing the
    oscilloscope voltage action potential spikes, the 20-second countdown memory window,
    and single-touch raindrop dissipation.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = int(duration * VIDEO_FPS)
    
    font_title = get_font(40, bold=True)
    font_sub = get_font(24, mono=True)
    font_label = get_font(28, bold=True)
    font_big = get_font(52, bold=True)
    font_small = get_font(20, mono=True)
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    raw_video_path = output_path.with_suffix(".temp.mp4")
    out_video = cv2.VideoWriter(str(raw_video_path), fourcc, VIDEO_FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))
    
    for frame_idx in range(total_frames):
        t = frame_idx / VIDEO_FPS
        frame = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 16, 26))
        draw = ImageDraw.Draw(frame)
        
        # Grid lines
        for gx in range(0, VIDEO_WIDTH, 80):
            draw.line([(gx, 0), (gx, VIDEO_HEIGHT)], fill=(18, 30, 46), width=1)
        for gy in range(0, VIDEO_HEIGHT, 80):
            draw.line([(0, gy), (VIDEO_WIDTH, gy)], fill=(18, 30, 46), width=1)

        # Header HUD
        draw.rectangle([50, 60, VIDEO_WIDTH - 50, 190], fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(draw, (50, 60, VIDEO_WIDTH - 50, 190), (0, 220, 255), arm_len=18, width=2)
        draw.text((80, 80), "DUAL-ACTION POTENTIAL MEMORY", fill=(255, 255, 255), font=font_title)
        draw.text((80, 140), "MECHANICAL THRESHOLD: 2 TOUCHES WITHIN 20 SECONDS", fill=(0, 210, 255), font=font_sub)

        # Oscilloscope Voltage Screen (Center-Top)
        osc_bbox = (50, 220, VIDEO_WIDTH - 50, 800)
        draw.rectangle(osc_bbox, fill=(6, 12, 20), outline=(0, 180, 230), width=2)
        draw_hud_bracket(draw, osc_bbox, (0, 220, 255), arm_len=24, width=2)
        draw.text((80, 240), "ACTION POTENTIAL VOLTAGE TRACE (mV)", fill=(0, 210, 255), font=font_sub)
        
        # Zero line (-120mV baseline)
        base_y = 660
        draw.line([(80, base_y), (VIDEO_WIDTH - 80, base_y)], fill=(40, 70, 95), width=2)
        draw.text((80, base_y + 10), "-120 mV (RESTING)", fill=(100, 140, 170), font=font_small)
        
        # Threshold line
        thresh_y = 380
        draw.line([(80, thresh_y), (VIDEO_WIDTH - 80, thresh_y)], fill=(220, 60, 60), width=2)
        draw.text((80, thresh_y - 30), "CRITICAL ACTIVATION THRESHOLD (+40 mV)", fill=(240, 80, 80), font=font_small)

        # Waveform generation across time
        wave_pts = []
        for x in range(80, VIDEO_WIDTH - 80, 4):
            norm_x = (x - 80) / (VIDEO_WIDTH - 160)
            wave_time = norm_x * 4.0 # 4 seconds on screen
            
            # Baseline noise
            vy = base_y + math.sin(x * 0.15 + t * 4) * 3
            
            # Spike 1 at 1.0s (Touch 1)
            if wave_time > 1.0:
                dt1 = wave_time - 1.0
                spike1 = math.exp(-dt1 * 4.0) * math.sin(dt1 * math.pi * 3) * 260
                vy -= max(0, spike1)
                
            # Spike 2 at 2.8s (Touch 2)
            if wave_time > 2.8:
                dt2 = wave_time - 2.8
                spike2 = math.exp(-dt2 * 3.5) * math.sin(dt2 * math.pi * 3) * 300
                vy -= max(0, spike2)
                
            wave_pts.append((x, int(vy)))
            
        if len(wave_pts) >= 2:
            draw.line(wave_pts, fill=(0, 255, 180), width=4)
            # Glowing scanline point
            scan_idx = int((t * 0.5) % 1.0 * len(wave_pts))
            sx, sy = wave_pts[scan_idx]
            draw.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], fill=(255, 255, 255), outline=(0, 255, 255), width=3)

        # Status text inside oscilloscope
        if t < 1.0:
            status_text = "STATUS: MONITORING TRIGGER HAIRS..."
            status_color = (120, 180, 220)
        elif t < 2.8:
            status_text = "PULSE 1 DETECTED (+160mV) -> MEMORY TIMER ENGAGED"
            status_color = (255, 220, 60)
        else:
            status_text = "PULSE 2 DETECTED! THRESHOLD SURPASSED -> SNAP INITIATED"
            status_color = (0, 255, 140)
        draw.text((80, 740), status_text, fill=status_color, font=font_label)

        # 20-Second Memory Window HUD (Middle)
        timer_bbox = (50, 840, VIDEO_WIDTH - 50, 1380)
        draw.rectangle(timer_bbox, fill=(15, 25, 40, 230), outline=(30, 80, 130), width=2)
        draw_hud_bracket(draw, timer_bbox, (0, 220, 255), arm_len=20, width=2)
        draw.text((80, 860), "CALCIUM CONCENTRATION & DECAY TIMER", fill=(120, 180, 240), font=font_sub)

        # Circular Countdown Timer
        timer_cx, timer_cy, timer_r = 250, 1110, 130
        draw.ellipse([timer_cx - timer_r, timer_cy - timer_r, timer_cx + timer_r, timer_cy + timer_r], outline=(40, 70, 100), width=8)
        
        # Countdown time calculation
        if t < 1.0:
            rem_sec = 20.0
            fill_pct = 0.0
        elif t < 2.8:
            rem_sec = max(0.0, 20.0 - (t - 1.0) * 2.2)
            fill_pct = (20.0 - rem_sec) / 20.0
        else:
            rem_sec = 0.10 # Snap time!
            fill_pct = 1.0
            
        arc_angle = int(fill_pct * 360)
        if arc_angle > 0:
            draw.arc([timer_cx - timer_r, timer_cy - timer_r, timer_cx + timer_r, timer_cy + timer_r], start=-90, end=-90 + arc_angle, fill=(0, 220, 255), width=10)
            
        draw.text((timer_cx - 85, timer_cy - 40), f"{rem_sec:.1f}s", fill=(255, 255, 255), font=font_big)
        draw.text((timer_cx - 65, timer_cy + 25), "WINDOW", fill=(120, 180, 240), font=font_sub)

        # Right-Hand Indicators
        rx = 450
        # Calcium Gauge
        draw.text((rx, 940), "CALCIUM ACCUMULATION [Ca2+]", fill=(140, 160, 190), font=font_small)
        draw.rectangle([rx, 975, VIDEO_WIDTH - 90, 1015], fill=(10, 20, 35), outline=(40, 80, 120), width=2)
        
        ca_fill = 0.15 if t < 1.0 else (0.55 if t < 2.8 else 1.0)
        fill_w = int((VIDEO_WIDTH - 90 - rx) * ca_fill)
        ca_color = (0, 210, 255) if ca_fill < 1.0 else (0, 255, 120)
        draw.rectangle([rx + 2, 977, rx + fill_w - 2, 1013], fill=ca_color)
        draw.text((rx + 15, 982), f"{int(ca_fill * 100)}%", fill=(10, 15, 25), font=font_sub)

        # Raindrop Filter Explanation Box
        draw.rectangle([rx, 1050, VIDEO_WIDTH - 90, 1330], fill=(10, 20, 35, 200), outline=(30, 60, 95), width=1)
        draw.text((rx + 20, 1070), "RAINDROP SAFETY FILTER:", fill=(255, 210, 80), font=font_label)
        bullets = [
            "1 Touch: Sub-threshold Ca2+",
            "20s Decay: Safe from rain",
            "2nd Touch: Rapid Bistable Snap",
            "Speed: 100ms Mechanical Buckling"
        ]
        for b_i, b_text in enumerate(bullets):
            draw.text((rx + 20, 1120 + b_i * 48), f"• {b_text}", fill=(200, 220, 245), font=font_small)

        np_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        out_video.write(np_frame)
        
    out_video.release()
    
    ffmpeg_exe = get_ffmpeg_binary()
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(raw_video_path.resolve()),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        str(output_path.resolve())
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    raw_video_path.unlink(missing_ok=True)
    return output_path

if __name__ == "__main__":
    p1 = CACHE_DIR / "test_trigger_hair.mp4"
    p2 = CACHE_DIR / "test_counting_timer.mp4"
    print("Generating test animations...")
    generate_trigger_hair_animation(p1, duration=3.0)
    generate_counting_timer_animation(p2, duration=3.0)
    print("Done generating test animations!")
