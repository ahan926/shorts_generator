import cv2
import os

artifact_dir = r"C:\Users\jpsh9\.gemini\antigravity\brain\f2ce8922-9ce1-4cea-ba35-4bd9d8177bed"

shorts = [
    ("nature_frog_elastic_tongue_catapult.mp4", [9.0, 18.0], ["frog_anim_compression", "frog_anim_strike"]),
    ("nature_sea_otter_fur_air_insulation.mp4", [9.0, 18.0], ["otter_anim_density", "otter_anim_air_barrier"]),
    ("nature_trap_jaw_ant_spring_mandibles.mp4", [10.0, 19.0], ["ant_anim_latch", "ant_anim_strike"]),
    ("nature_pit_viper_thermal_vision.mp4", [9.0, 18.0], ["viper_anim_loreal_pit", "viper_anim_thermal_projection"]),
    ("nature_archerfish_water_jet_mechanics.mp4", [9.0, 18.0], ["archerfish_anim_barrel", "archerfish_anim_bullet"]),
    ("nature_crocodile_death_roll_physics.mp4", [10.0, 19.0], ["crocodile_anim_bite", "crocodile_anim_death_roll"]),
    ("nature_electric_eel_biological_battery.mp4", [10.0, 19.0], ["eel_anim_electrocytes", "eel_anim_lightning"])
]

for filename, times, labels in shorts:
    path = os.path.join("output", filename)
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    for t, label in zip(times, labels):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if ret:
            out_name = f"{label}_verified.jpg"
            out_path = os.path.join(artifact_dir, out_name)
            cv2.imwrite(out_path, frame)
            print(f"Wrote {out_name}")
    cap.release()
print("Done extracting verification frames.")
