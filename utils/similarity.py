"""
similarity.py
=============

Meaning-preservation ("drift") checking between the original text and the
Gemini-rewritten text. Uses Gemini itself as a judge and returns a
structured, easy-to-render result.
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

import google.generativeai as genai

from utils.prompts import build_similarity_prompt
from utils.rewrite import GeminiClientError


@dataclass
class SimilarityResult:
    """Structured result of a meaning-preservation check."""

    score: int
    meaning_changed: bool
    explanation: str


def _extract_json(raw_text: str) -> dict:
    """
    Extract a JSON object from a raw model response, tolerating stray
    markdown code fences or surrounding text.

    Args:
        raw_text: The raw text returned by Gemini.

    Returns:
        A parsed dictionary.

    Raises:
        ValueError: If no valid JSON object could be located/parsed.
    """
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in the model response.")

    return json.loads(match.group(0))


def check_meaning_preservation(
    original: str,
    rewritten: str,
    model_name: Optional[str] = None,
) -> SimilarityResult:
    """
    Ask Gemini to score how well the rewritten text preserves the meaning
    of the original text.

    Args:
        original: The original source text.
        rewritten: The tone-shifted rewritten text.
        model_name: Optional override of the Gemini model to use.

    Returns:
        A SimilarityResult with a 0-100 score, a boolean flag for whether
        meaning changed materially, and a short explanation.

    Raises:
        GeminiClientError: If the API key is missing or the call fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiClientError(
            "GEMINI_API_KEY is not set. Please add it to your .env file "
            "(see .env.example)."
        )
    genai.configure(api_key=api_key)
    model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    prompt = build_similarity_prompt(original, rewritten)

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        raw_output = (response.text or "").strip()
        data = _extract_json(raw_output)
    except Exception as exc:  # noqa: BLE001
        raise GeminiClientError(f"Meaning-preservation check failed: {exc}") from exc

    score = int(data.get("similarity_score", 0))
    score = max(0, min(100, score))
    meaning_changed = bool(data.get("meaning_changed", score < 80))
    explanation = str(data.get("explanation", "")).strip() or "No explanation provided."

    return SimilarityResult(score=score, meaning_changed=meaning_changed, explanation=explanation)
