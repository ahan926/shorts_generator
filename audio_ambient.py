"""Procedural ambient audio generator for 100% royalty-free background pads."""
import math
import struct
import wave
from pathlib import Path

def generate_ambient_track(output_wav_path: Path, duration_sec: int = 60) -> Path:
    """
    Generates a gentle, warm ambient chord progression in standard stereo WAV.
    Completely procedural, zero copyright, zero royalties.
    """
    output_wav_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    total_samples = sample_rate * duration_sec
    
    # Warm harmonic frequencies (F minor 9 ambient pad: F2, C3, Ab3, Eb4, G4)
    freqs = [87.31, 130.81, 207.65, 311.13, 392.00]
    
    with wave.open(str(output_wav_path), "wb") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            # Slow subtle breathing modulation (LFO)
            lfo = 0.5 + 0.5 * math.sin(2 * math.pi * 0.15 * t)
            
            sample_val = 0.0
            for idx, f in enumerate(freqs):
                weight = 1.0 / (idx + 1)
                phase_drift = math.sin(0.05 * t * (idx + 1))
                sample_val += weight * math.sin(2 * math.pi * f * t + phase_drift)
                
            sample_val = (sample_val / len(freqs)) * lfo * 0.6
            
            # Smooth fade in and fade out
            fade_in = min(1.0, t / 3.0)
            fade_out = min(1.0, (duration_sec - t) / 3.0)
            sample_val *= fade_in * fade_out
            
            int_val = int(max(-32767, min(32767, sample_val * 32767)))
            # Stereo framing (slight left/right panning variance)
            frames.extend(struct.pack("<hh", int_val, int(int_val * 0.95)))
            
        wav_file.writeframes(frames)
        
    return output_wav_path
