"""Text-to-Speech engine using edge-tts (100% Free, High-Quality Neural Voices)."""
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import edge_tts
from config import DEFAULT_VOICE, VOICE_RATE, VOICE_PITCH

async def synthesize_speech(
    text: str,
    output_audio_path: Path,
    voice: str = DEFAULT_VOICE,
    rate: str = VOICE_RATE,
    pitch: str = VOICE_PITCH,
) -> Tuple[Path, List[Dict[str, Any]], float]:
    """
    Synthesizes speech using edge-tts and extracts exact word-level timestamps.
    
    Returns:
        Tuple of (output_audio_path, word_timings, total_duration)
    """
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
        pitch=pitch,
        boundary="WordBoundary"
    )
    words: List[Dict[str, Any]] = []
    
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            chunk_type = chunk.get("type")
            if chunk_type == "audio":
                audio_file.write(chunk["data"])
            elif chunk_type == "WordBoundary":
                # offset and duration are given in 100-nanosecond ticks (10,000,000 ticks = 1 second)
                offset_ticks = chunk["offset"]
                duration_ticks = chunk["duration"]
                text_word = chunk["text"]
                
                start_sec = offset_ticks / 10_000_000.0
                duration_sec = duration_ticks / 10_000_000.0
                end_sec = start_sec + duration_sec
                
                words.append({
                    "word": text_word,
                    "start": start_sec,
                    "end": end_sec,
                    "duration": duration_sec
                })

    # Estimate total duration from the last word or file
    total_duration = words[-1]["end"] + 0.4 if words else 0.0
    return output_audio_path, words, total_duration

def generate_voiceover(
    text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE
) -> Tuple[Path, List[Dict[str, Any]], float]:
    """Synchronous wrapper for synthesize_speech."""
    return asyncio.run(synthesize_speech(text, output_path, voice=voice))
