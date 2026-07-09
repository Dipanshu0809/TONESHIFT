"""
rewrite.py
==========

Core logic for communicating with the Gemini API to rewrite text
according to a selected tone, audience, and set of style controls.
"""

import os
from typing import Optional

import google.generativeai as genai

from utils.prompts import build_rewrite_prompt


class GeminiClientError(Exception):
    """Raised when the Gemini client cannot be configured or called."""


def _configure_gemini() -> str:
    """
    Configure the google.generativeai SDK using the GEMINI_API_KEY
    environment variable.

    Returns:
        The model name to use, read from GEMINI_MODEL or a sensible default.

    Raises:
        GeminiClientError: If no API key is found in the environment.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiClientError(
            "GEMINI_API_KEY is not set. Please add it to your .env file "
            "(see .env.example)."
        )
    genai.configure(api_key=api_key)
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def rewrite_text(
    text: str,
    tone: str,
    audience: str,
    formality: int = 50,
    length: int = 50,
    creativity: int = 50,
    model_name: Optional[str] = None,
) -> str:
    """
    Rewrite the given text using the Gemini API according to the requested
    tone, audience, and style sliders.

    Args:
        text: The original text supplied by the user.
        tone: Selected tone (e.g. "Professional", "Casual").
        audience: Selected target audience (e.g. "Student", "CEO").
        formality: 0-100 slider controlling formality.
        length: 0-100 slider controlling relative output length.
        creativity: 0-100 slider controlling stylistic creativity.
        model_name: Optional override of the Gemini model to use.

    Returns:
        The rewritten text as a plain string.

    Raises:
        GeminiClientError: If the API key is missing or the API call fails.
    """
    if not text or not text.strip():
        raise ValueError("Input text must not be empty.")

    default_model = _configure_gemini()
    model_name = model_name or default_model

    prompt = build_rewrite_prompt(
        text=text,
        tone=tone,
        audience=audience,
        formality=formality,
        length=length,
        creativity=creativity,
    )

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        output = (response.text or "").strip()
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI as a friendly error
        raise GeminiClientError(f"Gemini API request failed: {exc}") from exc

    if not output:
        raise GeminiClientError("Gemini returned an empty response. Please try again.")

    return output
