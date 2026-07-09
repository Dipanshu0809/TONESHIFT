"""
helpers.py
==========

Small, reusable helper functions: text statistics, readability estimation,
word-level diff highlighting, and rewrite-history management.
"""

import difflib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List

import textstat


@dataclass
class TextStats:
    """Basic statistics about a piece of text."""

    word_count: int
    char_count: int
    reading_time_seconds: int


def compute_text_stats(text: str, words_per_minute: int = 200) -> TextStats:
    """
    Compute word count, character count, and estimated reading time.

    Args:
        text: The text to analyze.
        words_per_minute: Assumed average adult reading speed.

    Returns:
        A TextStats object.
    """
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    reading_time_seconds = max(1, round((word_count / words_per_minute) * 60))
    return TextStats(
        word_count=word_count,
        char_count=char_count,
        reading_time_seconds=reading_time_seconds,
    )


def compute_readability(text: str) -> dict:
    """
    Estimate the readability level of a piece of text using the
    Flesch-Kincaid grade level and Flesch Reading Ease score.

    Args:
        text: The text to analyze.

    Returns:
        A dictionary with 'grade_level' and 'reading_ease' keys. Returns
        zeros for empty or whitespace-only text.
    """
    if not text or not text.strip():
        return {"grade_level": 0.0, "reading_ease": 0.0}

    try:
        grade_level = textstat.flesch_kincaid_grade(text)
        reading_ease = textstat.flesch_reading_ease(text)
    except Exception:  # noqa: BLE001 - textstat can be finicky on tiny inputs
        grade_level, reading_ease = 0.0, 0.0

    return {"grade_level": round(grade_level, 1), "reading_ease": round(reading_ease, 1)}


def highlight_word_diff(original: str, rewritten: str) -> str:
    """
    Build an HTML string highlighting word-level differences between the
    original and rewritten text. Words only in the rewritten text are
    wrapped in a <mark> tag.

    Args:
        original: The original text.
        rewritten: The rewritten text.

    Returns:
        An HTML-safe string with <mark> tags around changed/added words,
        suitable for rendering with st.markdown(..., unsafe_allow_html=True).
    """
    original_words = original.split()
    rewritten_words = rewritten.split()

    matcher = difflib.SequenceMatcher(a=original_words, b=rewritten_words)
    result_parts: List[str] = []

    for opcode, _, _, b_start, b_end in matcher.get_opcodes():
        chunk_words = rewritten_words[b_start:b_end]
        chunk_text = " ".join(_escape_html(w) for w in chunk_words)
        if opcode == "equal":
            result_parts.append(chunk_text)
        elif chunk_text:
            result_parts.append(f'<mark class="diff-highlight">{chunk_text}</mark>')

    return " ".join(part for part in result_parts if part)


def _escape_html(text: str) -> str:
    """Escape a small snippet of text for safe HTML rendering."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


@dataclass
class HistoryEntry:
    """A single rewrite stored in session history."""

    timestamp: str
    original: str
    rewritten: str
    tone: str
    audience: str
    similarity_score: int = field(default=0)

    def to_dict(self) -> dict:
        return asdict(self)


def new_history_entry(
    original: str,
    rewritten: str,
    tone: str,
    audience: str,
    similarity_score: int = 0,
) -> HistoryEntry:
    """
    Create a new HistoryEntry with the current UTC timestamp.

    Args:
        original: The original input text.
        rewritten: The rewritten output text.
        tone: Tone used for the rewrite.
        audience: Audience used for the rewrite.
        similarity_score: The meaning-preservation score, if computed.

    Returns:
        A populated HistoryEntry.
    """
    return HistoryEntry(
        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        original=original,
        rewritten=rewritten,
        tone=tone,
        audience=audience,
        similarity_score=similarity_score,
    )


def export_history_json(history: List[HistoryEntry]) -> str:
    """
    Serialize the full rewrite history to a pretty-printed JSON string.

    Args:
        history: List of HistoryEntry objects.

    Returns:
        A JSON string suitable for download.
    """
    return json.dumps([entry.to_dict() for entry in history], indent=2, ensure_ascii=False)


def build_meter_svg(score: int, needle_color: str = "#e8a33d") -> str:
    """
    Build an analog VU-meter-style SVG gauge for the meaning-preservation
    score, echoing the studio-console visual identity of the app.

    The gauge is a semicircular dial with a red -> amber -> teal gradient
    track and a rotating needle pointing to the current score.

    Args:
        score: Meaning-preservation score, 0-100.
        needle_color: Hex color for the needle and hub.

    Returns:
        A raw <svg> string ready to render with st.markdown(unsafe_allow_html=True).
    """
    score = max(0, min(100, score))
    angle = (score / 100) * 180 - 90  # -90deg (left) .. +90deg (right)

    svg = f"""
<svg viewBox="0 0 300 190" xmlns="http://www.w3.org/2000/svg" class="ts-meter-svg" role="img"
     aria-label="Meaning preservation meter showing {score} percent">
    <defs>
        <linearGradient id="meterTrackGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#f2545b" />
            <stop offset="50%" stop-color="#f0a500" />
            <stop offset="100%" stop-color="#4fd1c5" />
        </linearGradient>
    </defs>
    <path d="M 30 150 A 120 120 0 0 1 270 150" fill="none"
          stroke="url(#meterTrackGrad)" stroke-width="14" stroke-linecap="round"
          opacity="0.35" />
    <path d="M 30 150 A 120 120 0 0 1 270 150" fill="none"
          stroke="url(#meterTrackGrad)" stroke-width="14" stroke-linecap="round"
          stroke-dasharray="{(score / 100) * 377.0:.1f} 377" />
    <g class="ts-meter-needle" style="transform-origin: 150px 150px; transform: rotate({angle:.1f}deg);">
        <line x1="150" y1="150" x2="150" y2="42" stroke="{needle_color}" stroke-width="4"
              stroke-linecap="round" />
    </g>
    <circle cx="150" cy="150" r="9" fill="{needle_color}" />
    <text x="150" y="182" text-anchor="middle" class="ts-meter-label">MEANING METER</text>
</svg>
"""
    return svg.strip()
