"""Subtitle generation module producing modern, high-retention ASS subtitles."""
from pathlib import Path
from typing import List, Dict, Any
from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    SUBTITLE_FONT,
    SUBTITLE_FONT_SIZE,
    SUBTITLE_PRIMARY_COLOR,
    SUBTITLE_HIGHLIGHT_COLOR,
    SUBTITLE_OUTLINE_COLOR,
    SUBTITLE_OUTLINE_WIDTH,
    SUBTITLE_SHADOW_DEPTH,
    SUBTITLE_MARGIN_V,
)

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp: H:MM:SS.cc"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def clean_word(word: str) -> str:
    """Remove unwanted punctuation artifacts while keeping text punchy."""
    return word.strip()

def chunk_words(words: List[Dict[str, Any]], max_words_per_line: int = 3) -> List[List[Dict[str, Any]]]:
    """
    Groups words into short phrases (2-4 words) for fast, punchy mobile reading.
    Also breaks on strong punctuation (., !, ?).
    """
    chunks: List[List[Dict[str, Any]]] = []
    current_chunk: List[Dict[str, Any]] = []
    
    for item in words:
        current_chunk.append(item)
        word_text = item["word"]
        
        # End chunk if punctuation ends sentence or clause, or max words reached
        if (
            len(current_chunk) >= max_words_per_line
            or word_text.endswith((".", "!", "?", ";", ":", ","))
        ):
            chunks.append(current_chunk)
            current_chunk = []
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def generate_ass_subtitles(
    words: List[Dict[str, Any]],
    output_ass_path: Path,
    words_per_phrase: int = 3
) -> Path:
    """
    Generates an Advanced SubStation Alpha (.ass) subtitle file.
    Uses dynamic word-by-word yellow highlighting on white uppercase text.
    """
    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ASS Header
    ass_content = [
        "[Script Info]",
        "Title: YouTube Shorts Dynamic Captions",
        "ScriptType: v4.00+",
        f"PlayResX: {VIDEO_WIDTH}",
        f"PlayResY: {VIDEO_HEIGHT}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # Alignment 2 = Bottom-Center. MarginV places it in the vertical center safe zone.
        f"Style: Default,{SUBTITLE_FONT},{SUBTITLE_FONT_SIZE},{SUBTITLE_PRIMARY_COLOR},{SUBTITLE_HIGHLIGHT_COLOR},{SUBTITLE_OUTLINE_COLOR},&H80000000,-1,0,0,0,100,100,1,0,1,{SUBTITLE_OUTLINE_WIDTH},{SUBTITLE_SHADOW_DEPTH},2,60,180,{SUBTITLE_MARGIN_V},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    
    chunks = chunk_words(words, max_words_per_line=words_per_phrase)
    
    for chunk in chunks:
        if not chunk:
            continue
            
        # For each word in this chunk, create a dialogue line where that word is highlighted
        for i, target_word in enumerate(chunk):
            start_str = format_ass_time(target_word["start"])
            end_str = format_ass_time(target_word["end"])
            
            # Construct the phrase with the target word colored in highlight color
            formatted_tokens = []
            for j, w in enumerate(chunk):
                raw_text = clean_word(w["word"]).upper()
                if i == j:
                    # Highlight active word in Yellow with slight pop
                    formatted_tokens.append(f"{{\\c{SUBTITLE_HIGHLIGHT_COLOR}\\fscx110\\fscy110}}{raw_text}{{\\r}}")
                else:
                    # Inactive words in crisp White
                    formatted_tokens.append(f"{{\\c{SUBTITLE_PRIMARY_COLOR}\\fscx100\\fscy100}}{raw_text}{{\\r}}")
            
            line_text = " ".join(formatted_tokens)
            ass_content.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

    output_ass_path.write_text("\n".join(ass_content), encoding="utf-8")
    return output_ass_path
