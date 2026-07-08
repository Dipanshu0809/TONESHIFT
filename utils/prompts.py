"""
prompts.py
==========

Centralized prompt-engineering templates for ToneShift.

Keeping every prompt in one module makes it easy to iterate on prompt
quality without touching application or API-calling logic, and makes
the prompt-engineering work visible and reviewable on its own.
"""

# ---------------------------------------------------------------------------
# Tone descriptions
# ---------------------------------------------------------------------------
# Each tone maps to a short instruction fragment that steers Gemini's style
# without letting it drift into changing facts or content.
TONE_DESCRIPTIONS = {
    "Professional": (
        "formal, polished, and businesslike, using precise vocabulary and "
        "complete sentences suitable for a workplace setting"
    ),
    "Casual": (
        "relaxed, conversational, and informal, as if chatting with a friend, "
        "while remaining clear and respectful"
    ),
    "Friendly": (
        "warm, approachable, and encouraging, using a positive and personable "
        "voice"
    ),
    "Academic": (
        "scholarly and precise, using discipline-appropriate terminology, "
        "objective phrasing, and well-structured argumentation"
    ),
    "Executive": (
        "concise, high-level, and results-oriented, suitable for a busy "
        "senior leader who wants the key points quickly"
    ),
    "Persuasive": (
        "compelling and confident, using rhetorical techniques to convince "
        "the reader, without exaggerating or inventing facts"
    ),
    "Technical": (
        "precise, structured, and detail-oriented, using accurate technical "
        "terminology appropriate for a knowledgeable reader"
    ),
    "Creative": (
        "imaginative and vivid, using engaging language and figurative "
        "expression while keeping the underlying message intact"
    ),
}

# ---------------------------------------------------------------------------
# Audience descriptions
# ---------------------------------------------------------------------------
AUDIENCE_DESCRIPTIONS = {
    "Student": "a student who is learning and benefits from clear, guided explanations",
    "Child": "a young child, so the language must be very simple, short, and easy to picture",
    "Teacher": "a teacher who values clarity, structure, and pedagogical framing",
    "Customer": "a customer who wants clear, helpful, and respectful communication",
    "Manager": "a manager who wants practical, actionable, and time-efficient information",
    "CEO": "a CEO who wants a high-level summary focused on outcomes and impact",
    "Developer": "a software developer who is comfortable with technical language and precision",
    "General Public": "a general audience with no specialized background knowledge",
}


def build_rewrite_prompt(
    text: str,
    tone: str,
    audience: str,
    formality: int,
    length: int,
    creativity: int,
) -> str:
    """
    Build the main rewrite prompt sent to Gemini.

    The prompt is engineered to strictly preserve facts, names, numbers,
    and dates while only adjusting tone, style, and phrasing to suit the
    requested tone and audience.

    Args:
        text: The original text to rewrite.
        tone: Target tone (must be a key in TONE_DESCRIPTIONS).
        audience: Target audience (must be a key in AUDIENCE_DESCRIPTIONS).
        formality: Slider value 0-100, higher = more formal.
        length: Slider value 0-100, higher = longer/more elaborate output.
        creativity: Slider value 0-100, higher = more creative freedom in phrasing.

    Returns:
        A fully formatted prompt string ready to send to the Gemini API.
    """
    tone_desc = TONE_DESCRIPTIONS.get(tone, tone)
    audience_desc = AUDIENCE_DESCRIPTIONS.get(audience, audience)

    length_instruction = (
        "significantly shorter and more condensed than the original"
        if length < 33
        else "similar in length to the original"
        if length < 66
        else "more elaborated and expanded than the original, while staying relevant"
    )

    formality_instruction = (
        "very informal and relaxed"
        if formality < 33
        else "moderately formal"
        if formality < 66
        else "highly formal and polished"
    )

    creativity_instruction = (
        "very literal, with minimal stylistic embellishment"
        if creativity < 33
        else "moderately expressive, with some stylistic variety"
        if creativity < 66
        else "highly creative and expressive in phrasing, word choice, and rhythm"
    )

    prompt = f"""You are an expert editor specializing in tone and audience adaptation.

Rewrite the TEXT below so that it:
- Uses a {tone_desc} tone.
- Is written for {audience_desc}.
- Is {length_instruction} (length control: {length}/100).
- Is {formality_instruction} (formality control: {formality}/100).
- Is {creativity_instruction} (creativity control: {creativity}/100).

STRICT RULES (do not break these under any circumstance):
1. NEVER change the factual meaning of the text.
2. NEVER add facts, claims, or details that are not present in the original.
3. NEVER remove important facts, claims, or details from the original.
4. ALWAYS preserve all proper names exactly as written.
5. ALWAYS preserve all numbers, statistics, and quantities exactly as written.
6. ALWAYS preserve all dates and time references exactly as written.
7. Only adjust vocabulary, sentence structure, tone, and style to match the
   requested tone and audience.
8. Return ONLY the rewritten text. Do not include explanations, notes,
   headers, quotation marks, or any text other than the rewritten version.

TEXT:
\"\"\"
{text}
\"\"\"

REWRITTEN TEXT:"""
    return prompt


def build_similarity_prompt(original: str, rewritten: str) -> str:
    """
    Build a prompt that asks Gemini to score meaning preservation between
    the original and rewritten text ("drift" check).

    Args:
        original: The original source text.
        rewritten: The rewritten (tone-shifted) text.

    Returns:
        A prompt string instructing Gemini to return a strict JSON object.
    """
    prompt = f"""You are a meaning-preservation auditor. Compare the ORIGINAL text
and the REWRITTEN text below and evaluate whether the rewritten version
preserves the same facts, meaning, names, numbers, and dates as the original.

Respond with ONLY a valid JSON object (no markdown, no code fences, no extra
text) in exactly this format:

{{
  "similarity_score": <integer from 0 to 100>,
  "meaning_changed": <true or false>,
  "explanation": "<one or two concise sentences explaining your score>"
}}

Scoring guide:
- 95-100: Meaning, facts, names, numbers, and dates are fully preserved.
- 80-94: Meaning is preserved but phrasing/emphasis shifted slightly.
- 50-79: Some nuance, detail, or emphasis was lost or altered.
- Below 50: The meaning has materially changed, or facts/numbers/names/dates
  were altered, added, or removed.

ORIGINAL:
\"\"\"
{original}
\"\"\"

REWRITTEN:
\"\"\"
{rewritten}
\"\"\"

JSON RESPONSE:"""
    return prompt
