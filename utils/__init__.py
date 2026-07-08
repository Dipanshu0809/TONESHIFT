"""
utils
=====

Internal package for the ToneShift application.

Modules:
    prompts     -- Prompt-engineering templates sent to the Gemini API.
    rewrite     -- Core rewriting logic (calls Gemini, parses responses).
    similarity  -- Meaning-preservation ("drift") scoring.
    pdf_export  -- Utilities for exporting rewritten text as a PDF.
    helpers     -- Small, reusable helper functions (stats, diffing, etc.).
"""
