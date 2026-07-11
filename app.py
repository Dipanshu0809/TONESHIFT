"""
app.py
======

ToneShift - Audience-Aware Rewriter
A Streamlit application that rewrites user text into different tones and
for different audiences using the Gemini API, while preserving meaning.

Run with:
    streamlit run app.py
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

from utils.helpers import (
    build_meter_svg,
    compute_readability,
    compute_text_stats,
    export_history_json,
    highlight_word_diff,
    new_history_entry,
)
from utils.pdf_export import build_pdf
from utils.rewrite import GeminiClientError, rewrite_text
from utils.similarity import check_meaning_preservation
from auth import login_page

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv()

APP_DIR = Path(__file__).parent
TONES = [
    "Professional", "Casual", "Friendly", "Academic",
    "Executive", "Persuasive", "Technical", "Creative",
]
AUDIENCES = [
    "Student", "Child", "Teacher", "Customer",
    "Manager", "CEO", "Developer", "General Public",
]

DARK_OVERRIDES = """
<style>
:root {
    --ts-bg: #12141a;
    --ts-panel: #1b1e27;
    --ts-panel-alt: #242833;
    --ts-rack: #0d0f14;
    --ts-border: #333748;
    --ts-text: #eef0f5;
    --ts-text-muted: #9198ab;
    --ts-text-on-rack: #eef0f5;
    --ts-text-on-rack-muted: #767c8c;
    --ts-accent: #e8a33d;
    --ts-accent-strong: #ffb84d;
    --ts-secondary: #4fd1c5;
    --ts-danger: #f2545b;
    --ts-warn: #f0a500;
    --ts-highlight-bg: #4a3200;
    --ts-highlight-text: #ffdf9e;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: var(--ts-panel) !important;
    border-right: 1px solid var(--ts-border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--ts-text) !important;
}

/* ---- Every native widget label (sidebar + main) ---- */
div[data-testid="stWidgetLabel"] p,
div[data-testid="stWidgetLabel"] label,
label,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: var(--ts-text) !important;
}
[data-testid="stCaptionContainer"] {
    color: var(--ts-text-muted) !important;
}


/* ---- File uploader ---- */
[data-testid="stFileUploaderDropzone"] {
    background: var(--ts-panel-alt) !important;
    border-color: var(--ts-border) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] * {
    color: var(--ts-text-muted) !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: var(--ts-panel) !important;
    color: var(--ts-text) !important;
    border-color: var(--ts-border) !important;
}

/* ---- Slider / radio value text ---- */
[data-testid="stSlider"] div,
[data-testid="stRadio"] label p {
    color: var(--ts-text) !important;
}

/* ---- Text area placeholder ---- */
.stTextArea textarea::placeholder {
    color: var(--ts-text-muted) !important;
    opacity: 1 !important;
}

/* ---- Alerts (info/success/warning/error boxes) ---- */
[data-testid="stAlert"] {
    background: var(--ts-panel-alt) !important;
}
[data-testid="stAlert"] p {
    color: var(--ts-text) !important;
}
/* ===== FINAL SELECTBOX FIX ===== */

.stSelectbox input {
    background: #263142 !important;
    color: white !important;
    -webkit-text-fill-color: white !important;
}

.stSelectbox input[role="combobox"] {
    background: #263142 !important;
    color: white !important;
    -webkit-text-fill-color: white !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    background: #263142 !important;
    border: 1px solid #3b4b62 !important;
    border-radius: 10px !important;
}

.stSelectbox svg {
    fill: white !important;
}

/* Fix the dropdown arrow container */
.stSelectbox button {
    background: #263142 !important;
    border: none !important;
    color: white !important;
}

/* Arrow icon */
.stSelectbox button svg {
    fill: white !important;
}

/* Right side of selectbox */
.stSelectbox [data-baseweb="select"] button {
    background: #263142 !important;
}

/* Entire selectbox */
.stSelectbox [data-baseweb="select"] {
    background: #263142 !important;
    border-radius: 10px !important;
}

</style>
"""

FONT_IMPORTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
"""


def load_css() -> None:
    """Load web fonts, the base stylesheet, and (if selected) dark-mode overrides."""
    st.markdown(FONT_IMPORTS, unsafe_allow_html=True)
    css_path = APP_DIR / "styles" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
    if st.session_state.get("theme", "Light") == "Dark":
        st.markdown(DARK_OVERRIDES, unsafe_allow_html=True)


def init_session_state() -> None:
    """Initialize all Streamlit session_state keys used across the app."""
    defaults = {
        "theme": "Light",
        "rewritten_text": "",
        "original_text": "",
        "similarity_result": None,
        "history": [],
        "tone": TONES[0],
        "audience": AUDIENCES[0],
        "logged_in": False,
        "username": ""
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def render_header() -> None:
    """Render the console-style header rack (the app's signature visual)."""
    st.markdown(
        """
        <div class="ts-rack">
            <div class="ts-rack-eyebrow">Audience-Aware Rewrite Console</div>
            <h1>ToneShift</h1>
            <p>Dial in a tone, a listener, and a style — get text remastered
            to fit, with every fact, name, and number still intact.</p>
            <div class="ts-rack-tag">MODEL&nbsp;TS&#8209;1 &middot; ENGINE: GEMINI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict:
    """
    Render the sidebar controls (theme toggle, tone/audience, sliders,
    API key status) and return the selected configuration.

    Returns:
        A dictionary of the current control values.
    """
    with st.sidebar:
        st.success(f"👋 Welcome, {st.session_state.username}")
        st.markdown("### ⚙️ Settings")

        theme = st.radio("Appearance", ["Light", "Dark"], horizontal=True,
                          index=0 if st.session_state.theme == "Light" else 1)
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()

        
        st.markdown("---")
        st.markdown("### 🎭 Tone & Audience")
        tone = st.selectbox("Tone", TONES, index=TONES.index(st.session_state.tone))
        audience = st.selectbox("Target Audience", AUDIENCES,
                                 index=AUDIENCES.index(st.session_state.audience))

        st.markdown("### 🎚️ Style Controls")
        formality = st.slider("Formality", 0, 100, 50, help="0 = very informal, 100 = very formal")
        length = st.slider("Length", 0, 100, 50, help="0 = shorter, 100 = longer/expanded")
        creativity = st.slider("Creativity", 0, 100, 50, help="0 = literal, 100 = highly expressive")

        st.markdown("---")
        st.markdown("### 🕘 Rewrite History")
        if not st.session_state.history:
            st.caption("No rewrites yet. Your history will appear here.")
        else:
            for entry in reversed(st.session_state.history[-8:]):
                st.markdown(
                    f"""
                    <div class="ts-history-item">
                        <div class="meta">{entry.timestamp} · {entry.tone} → {entry.audience}
                        · {entry.similarity_score}% match</div>
                        {entry.rewritten[:90]}{"…" if len(entry.rewritten) > 90 else ""}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            history_json = export_history_json(st.session_state.history)
            st.download_button(
                "⬇️ Export Full History (JSON)",
                data=history_json,
                file_name="toneshift_history.json",
                mime="application/json",
                use_container_width=True,
            )
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.history = []
                st.rerun()
        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""

    # Optional: Clear user-specific data
            st.session_state.rewritten_text = ""
            st.session_state.original_text = ""
            st.session_state.similarity_result = None
            st.session_state.history = []
            if hasattr(st.user, "is_logged_in") and st.user.is_logged_in:
                st.logout()
            st.rerun()
            
    return {
        "tone": tone,
        "audience": audience,
        "formality": formality,
        "length": length,
        "creativity": creativity,
    }


def render_score_chip(score: int) -> str:
    """Return an HTML status chip styled according to the similarity score band."""
    if score >= 85:
        css_class, label = "ts-chip-high", "STRONG MATCH"
    elif score >= 60:
        css_class, label = "ts-chip-medium", "MINOR DRIFT"
    else:
        css_class, label = "ts-chip-low", "MEANING CHANGED"
    return f'<span class="ts-chip {css_class}">&#9679; {label}</span>'


def render_stats_row(text: str) -> None:
    """Render a row of word count / char count / reading time / readability metrics."""
    stats = compute_text_stats(text)
    readability = compute_readability(text)
    st.markdown(
        f"""
        <div class="ts-metric-row">
            <div class="ts-metric"><div class="value">{stats.word_count}</div>
                <div class="label">Words</div></div>
            <div class="ts-metric"><div class="value">{stats.char_count}</div>
                <div class="label">Characters</div></div>
            <div class="ts-metric"><div class="value">{stats.reading_time_seconds}s</div>
                <div class="label">Reading Time</div></div>
            <div class="ts-metric"><div class="value">{readability['grade_level']}</div>
                <div class="label">Grade Level</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application entry point."""
    st.set_page_config(
        page_title="ToneShift — Audience-Aware Rewriter",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()

    if not st.session_state.logged_in:
        login_page()
        return

    controls = render_sidebar()
    load_css()
    render_header()

    col_input, col_output = st.columns(2, gap="large")

    clear_clicked = False
    rewrite_clicked = False

    # ---------------------------- Input column ----------------------------
    with col_input:
        with st.container(border=True):
            st.markdown(
                '<div class="ts-channel-head"><span class="ts-led ts-led-input"></span>'
                '<span class="ts-label">Channel 1 &middot; Input</span></div>',
                unsafe_allow_html=True,
            )
            uploaded_file = st.file_uploader(
                "Upload File",
                type=["txt", "pdf", "docx"],
            )

            file_text = ""

            if uploaded_file is not None:
                # TXT
                if uploaded_file.name.endswith(".txt"):
                    file_text = uploaded_file.read().decode("utf-8")

                # PDF
                elif uploaded_file.name.endswith(".pdf"):
                    reader = PdfReader(uploaded_file)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            file_text += text + "\n"

                # DOCX
                elif uploaded_file.name.endswith(".docx"):
                    doc = Document(uploaded_file)
                    for para in doc.paragraphs:
                        file_text += para.text + "\n"

                st.session_state["original_text_input"] = file_text

            original_text = st.text_area(
                "",
                key="original_text_input",
                height=260,
                placeholder="Paste or type the text you want to rewrite…",
                label_visibility="collapsed",
            )
            render_stats_row(original_text)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                rewrite_clicked = st.button(
                    "✨ Rewrite Text",
                    key="rewrite_btn",
                    type="primary",
                    use_container_width=True,
                )
            with btn_col2:
                clear_clicked = st.button(
                    "🧹 Clear",
                    key="clear_btn",
                    use_container_width=True,
                )

    if clear_clicked:
        st.session_state.rewritten_text = ""
        st.session_state.original_text = ""
        st.session_state.similarity_result = None
        st.rerun()

    if rewrite_clicked:
        if not original_text or not original_text.strip():
            st.warning("Please enter some text before rewriting.")
        else:
            with st.spinner("ToneShift is rewriting your text with Gemini…"):
                try:
                    rewritten = rewrite_text(
                        text=original_text,
                        tone=controls["tone"],
                        audience=controls["audience"],
                        formality=controls["formality"],
                        length=controls["length"],
                        creativity=controls["creativity"],
                    )
                    st.session_state.rewritten_text = rewritten
                    st.session_state.original_text = original_text
                    st.session_state.tone = controls["tone"]
                    st.session_state.audience = controls["audience"]

                    with st.spinner("Checking meaning preservation…"):
                        similarity = check_meaning_preservation(original_text, rewritten)
                        st.session_state.similarity_result = similarity

                    entry = new_history_entry(
                        original=original_text,
                        rewritten=rewritten,
                        tone=controls["tone"],
                        audience=controls["audience"],
                        similarity_score=similarity.score,
                    )
                    st.session_state.history.append(entry)
                    st.success("Rewrite complete!", icon="✅")
                except GeminiClientError as exc:
                    st.error(f"Gemini API error: {exc}", icon="🚫")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Unexpected error: {exc}", icon="🚫")

    # ---------------------------- Output column ----------------------------
    with col_output:
        with st.container(border=True):
            st.markdown(
                '<div class="ts-channel-head"><span class="ts-led ts-led-output"></span>'
                '<span class="ts-label">Channel 2 &middot; Output</span></div>',
                unsafe_allow_html=True,
            )

            rewritten_text = st.session_state.rewritten_text
            if rewritten_text:
                st.markdown(f'<div class="ts-text-box">{rewritten_text}</div>', unsafe_allow_html=True)
                render_stats_row(rewritten_text)

                copy_col, txt_col, pdf_col = st.columns(3)
                with copy_col:
                    if st.button("📋 Copy Output", use_container_width=True):
                        st.toast("Select the text above and copy with Ctrl/Cmd+C", icon="📋")
                with txt_col:
                    st.download_button(
                        "⬇️ Download .TXT",
                        data=rewritten_text,
                        file_name="toneshift_output.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with pdf_col:
                    pdf_bytes = build_pdf(
                        rewritten=rewritten_text,
                        original=st.session_state.original_text,
                        tone=st.session_state.tone,
                        audience=st.session_state.audience,
                    )
                    st.download_button(
                        "⬇️ Download .PDF",
                        data=pdf_bytes,
                        file_name="toneshift_output.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.info("Your rewritten text will appear here after you click **Rewrite Text**.")

    # ---------------------------- Comparison & analysis ----------------------------
    if st.session_state.rewritten_text:
        with st.container(border=True):
            st.markdown("#### 🔍 Side-by-Side Comparison & Diff Highlight")
            diff_html = highlight_word_diff(
                st.session_state.original_text, st.session_state.rewritten_text
            )
            cmp_col1, cmp_col2 = st.columns(2)
            with cmp_col1:
                st.markdown(
                    '<div class="ts-channel-head"><span class="ts-led ts-led-input"></span>'
                    '<span class="ts-label">Original Signal</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ts-text-box">{st.session_state.original_text}</div>',
                    unsafe_allow_html=True,
                )
            with cmp_col2:
                st.markdown(
                    '<div class="ts-channel-head"><span class="ts-led ts-led-output"></span>'
                    '<span class="ts-label">Rewritten Signal &middot; changes highlighted</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="ts-text-box">{diff_html}</div>', unsafe_allow_html=True)

        similarity = st.session_state.similarity_result
        if similarity:
            with st.container(border=True):
                st.markdown(
                    '<div class="ts-channel-head"><span class="ts-label">Meaning Preservation Check</span></div>',
                    unsafe_allow_html=True,
                )
                meter_svg = build_meter_svg(similarity.score)
                st.markdown(
                    f"""
                    <div class="ts-meter-wrap">
                        {meter_svg}
                        <div class="ts-meter-score">{similarity.score}%</div>
                        {render_score_chip(similarity.score)}
                        <div class="ts-meter-verdict">{similarity.explanation}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
if __name__ == "__main__":
    # Check Auth Session State first
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        login_page()
    else:
        main()