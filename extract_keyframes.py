import subprocess
import os
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
output_dir = r"C:\Users\jpsh9\.gemini\antigravity\scratch\shorts_generator\output"
art_dir = r"C:\Users\jpsh9\.gemini\antigravity\brain\f2ce8922-9ce1-4cea-ba35-4bd9d8177bed"

shorts = [
    ("nature_frog_elastic_tongue_catapult.mp4", "frog"),
    ("nature_sea_otter_fur_air_insulation.mp4", "otter"),
    ("nature_trap_jaw_ant_spring_mandibles.mp4", "ant"),
    ("nature_pit_viper_thermal_vision.mp4", "viper"),
    ("nature_archerfish_water_jet_mechanics.mp4", "archerfish"),
    ("nature_crocodile_death_roll_physics.mp4", "crocodile"),
    ("nature_electric_eel_biological_battery.mp4", "eel")
]

for video_name, prefix in shorts:
    video_path = os.path.join(output_dir, video_name)
    out_1 = os.path.join(art_dir, f"stock_short_{prefix}_1.jpg")
    out_2 = os.path.join(art_dir, f"stock_short_{prefix}_2.jpg")
    
    subprocess.run([ffmpeg_exe, "-y", "-ss", "00:00:03.000", "-i", video_path, "-vframes", "1", "-q:v", "2", out_1], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([ffmpeg_exe, "-y", "-ss", "00:00:15.000", "-i", video_path, "-vframes", "1", "-q:v", "2", out_2], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Extracted frames for {prefix}")

print("All keyframes successfully extracted!")
