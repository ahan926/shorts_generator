import numpy as np
import wave
from pathlib import Path

def generate_sub_impact(output_path: Path, duration: float = 1.4, sample_rate: int = 44100):
    """Generates a deep cinematic sub-bass impact/boom."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Exponential frequency drop from 95Hz to 32Hz
    freq = 95.0 * np.exp(-3.5 * t) + 32.0
    phase = 2.0 * np.pi * np.cumsum(freq) / sample_rate
    
    # Sub wave + gentle octave harmonic
    sub = np.sin(phase) + 0.35 * np.sin(2.0 * phase)
    
    # Fast punch attack (8ms) followed by smooth exponential decay
    env = np.where(t < 0.008, t / 0.008, np.exp(-3.2 * (t - 0.008)))
    signal = sub * env * 0.85
    
    # Soft clip saturation for warmth
    signal = np.tanh(signal * 1.5) / 1.5
    
    # Convert to 16-bit PCM stereo
    pcm = (signal * 32767).astype(np.int16)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        # Stereo duplicate
        stereo = np.column_stack((pcm, pcm))
        wf.writeframes(stereo.tobytes())
    return output_path

def generate_whoosh(output_path: Path, duration: float = 0.40, sample_rate: int = 44100):
    """Generates an airy, punchy transition whoosh using filtered modulated noise."""
    total_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, total_samples, endpoint=False)
    
    # White noise
    noise = np.random.uniform(-1.0, 1.0, total_samples)
    
    # Amplitude envelope: bell curve peaking around 60% of duration
    env = np.sin(np.pi * (t / duration) ** 1.2) ** 2
    
    # Frequency sweep modulation
    center_freq = 200.0 + 2200.0 * np.sin(np.pi * t / duration)
    carrier = np.sin(2.0 * np.pi * np.cumsum(center_freq) / sample_rate)
    
    signal = noise * 0.45 * env + carrier * 0.25 * env
    signal = np.clip(signal, -1.0, 1.0) * 0.70
    
    pcm = (signal * 32767).astype(np.int16)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        stereo = np.column_stack((pcm, pcm))
        wf.writeframes(stereo.tobytes())
    return output_path

if __name__ == "__main__":
    out_dir = Path("cache/sfx")
    generate_sub_impact(out_dir / "impact_boom.wav")
    generate_whoosh(out_dir / "whoosh_01.wav")
    print("Generated procedural SFX in cache/sfx!")
