"""
pdf_export.py
=============

Utilities for exporting rewritten text (optionally alongside the original)
as a clean, shareable PDF document using fpdf2.
"""

from datetime import datetime
from io import BytesIO

from fpdf import FPDF


class ToneShiftPDF(FPDF):
    """A lightly styled PDF document for ToneShift exports."""

    def header(self) -> None:  # noqa: D102 - inherited docstring/behavior from FPDF
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "ToneShift - Rewritten Text Export", ln=True, align="C")
        self.set_draw_color(200, 200, 200)
        self.line(10, 20, 200, 20)
        self.ln(6)

    def footer(self) -> None:  # noqa: D102
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _write_section(pdf: FPDF, title: str, body: str) -> None:
    """Write a titled section of text into the PDF."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, title, ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    safe_body = body.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 6, safe_body)
    pdf.ln(4)


def build_pdf(
    rewritten: str,
    original: str = "",
    tone: str = "",
    audience: str = "",
    include_original: bool = True,
) -> bytes:
    """
    Build a PDF document containing the rewritten text (and optionally the
    original text for comparison), along with basic metadata.

    Args:
        rewritten: The rewritten text to export.
        original: The original text, included if include_original is True.
        tone: The tone used for the rewrite, shown in the metadata line.
        audience: The audience used for the rewrite, shown in the metadata line.
        include_original: Whether to include the original text section.

    Returns:
        Raw PDF bytes, ready to be offered via a Streamlit download button.
    """
    pdf = ToneShiftPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    meta_line = f"Tone: {tone or 'N/A'}    |    Audience: {audience or 'N/A'}    |    Generated: " \
                f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 6, meta_line)
    pdf.ln(4)

    if include_original and original.strip():
        _write_section(pdf, "Original Text", original)

    _write_section(pdf, "Rewritten Text", rewritten)

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1", "replace")
    return bytes(output)


def build_pdf_bytesio(*args, **kwargs) -> BytesIO:
    """
    Convenience wrapper around build_pdf that returns a BytesIO buffer,
    which some Streamlit download flows prefer over raw bytes.

    Args/Returns mirror build_pdf, wrapped in a BytesIO object.
    """
    return BytesIO(build_pdf(*args, **kwargs))
