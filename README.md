<p align="center">
  <img src="assets/logo.png" width="110" alt="ToneShift logo" />
</p>

<h1 align="center">ToneShift — Audience-Aware Rewriter</h1>

<p align="center">
  An AI-powered writing assistant that rewrites text into different tones and
  for different audiences — while proving, not just claiming, that the
  original meaning is preserved.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.42%2B-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="Gemini API" src="https://img.shields.io/badge/Gemini-API-8E7BFF?logo=googlegemini&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

---

## 📖 Project Overview

**ToneShift** is a full-stack, AI-engineering portfolio project built with
Streamlit and the Google **Gemini API**. It lets users paste any piece of
text, choose a **tone** (e.g. Professional, Casual, Academic) and a
**target audience** (e.g. Student, CEO, Developer), and instantly get a
rewritten version tailored to that combination — all while **guaranteeing
factual meaning is preserved**: names, numbers, dates, and claims are never
altered, only the style and phrasing are.

The project goes beyond a simple prompt wrapper. It includes prompt
engineering safeguards, an automated **meaning-drift check** scored by
Gemini itself, word-level diff highlighting, readability analysis, a full
rewrite history with export, and its own **user account system** — with
both classic email/password accounts and **Google Sign-In** — the kind of
end-to-end feature set expected of a production-quality AI application.

---

## ✨ Features

### Core
- Rewrite text into **8 tones**: Professional, Casual, Friendly, Academic,
  Executive, Persuasive, Technical, Creative.
- Adapt output for **8 audiences**: Student, Child, Teacher, Customer,
  Manager, CEO, Developer, General Public.
- **Formality**, **Length**, and **Creativity** sliders for fine-grained
  control over the rewrite.
- Strict meaning preservation — names, numbers, and dates are never changed.
- **Rewrite**, **Clear**, **Copy Output**, **Download as TXT**, and
  **Download as PDF** actions.
- Upload source text directly from **TXT, PDF, or DOCX** files.

### Advanced
- 🔀 **Side-by-side comparison** of original vs. rewritten text.
- 🖍️ **Word-level diff highlighting** of changed/added text.
- 🧠 **Meaning Preservation Check** — Gemini scores similarity (0–100%) and
  explains whether/why meaning changed, shown on a visual meter.
- 📊 **Readability score** (Flesch-Kincaid grade level & reading ease).
- 🔢 **Word count**, **character count**, and **estimated reading time**.
- 🕘 **Rewrite history** tracked per session.
- 🌗 **Light / Dark mode** toggle with a custom, console-styled UI.

### Accounts & Security
- 🔐 **Sign up / Sign in** with SQLite + `bcrypt`-hashed passwords (never
  stored in plain text).
- 🔵 **"Continue with Google"** — native OAuth login via Streamlit's
  built-in `st.login()`, powered by Authlib. Google-authenticated users are
  automatically synced into the same user table as password accounts.
- Session-based login state — the rewrite workspace is only reachable once
  authenticated, by either method.
- Per-user welcome greeting in the sidebar (shows name/email for Google
  users, username for password accounts).

---

## 🛠️ Tech Stack

| Layer      | Technology                                   |
|------------|-----------------------------------------------|
| Frontend   | Streamlit, custom CSS (console/rack-styled UI), light & dark themes |
| Backend    | Python 3.10+, modular utility architecture    |
| Auth       | SQLite + `bcrypt` (password accounts), Streamlit native OAuth + `Authlib` (Google Sign-In) |
| AI Model   | Google Gemini API (`google-generativeai`)     |
| PDF Export | `fpdf2`                                       |
| File Import| `pypdf`, `python-docx`                        |
| Readability| `textstat`                                    |
| Config     | `python-dotenv`, Streamlit `secrets.toml`      |

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/ToneShift.git
cd ToneShift

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies (includes Streamlit's auth extra + Authlib)
pip install -r requirements.txt

# 4. Configure environment variables (see below)
cp .env.example .env
# then edit .env and add your Gemini API key

# 5. (Optional) Set up Google Sign-In — see "Google OAuth Setup" below

# 6. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`. On first launch you'll land
on the **Sign In / Create Account** screen — create an account (or use
"Continue with Google", if configured) to reach the main rewrite workspace.
The user database (`users.db`) is created automatically on first run.

---

## 🔑 Environment Variables

Create a `.env` file in the project root (use `.env.example` as a template):

| Variable         | Description                                              | Example              |
|------------------|-------------------------------------------------------------|----------------------|
| `GEMINI_API_KEY` | Your Google Gemini API key (required)                     | `AIza...`            |
| `GEMINI_MODEL`   | Gemini model to use (optional, defaults to `gemini-2.5-flash`) | `gemini-2.5-pro` |

Get a free Gemini API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

> ⚠️ Never commit your real `.env` file or `users.db`. Both are already
> excluded via `.gitignore` — only `.env.example` should be tracked.

---

## 🔵 Google OAuth Setup (optional)

"Continue with Google" requires its own config, separate from `.env`:

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project → set up the **OAuth consent screen** (Audience: External) →
   create an **OAuth 2.0 Client ID** (type: Web application) with an
   authorized redirect URI of `http://localhost:8501/oauth2callback`
   (for local dev).
2. Create `.streamlit/secrets.toml` (copy from `secrets.toml.example`) and
   fill in your real `client_id` / `client_secret`, plus any random string
   for `cookie_secret`:

   ```toml
   [auth]
   redirect_uri = "http://localhost:8501/oauth2callback"
   cookie_secret = "a-long-random-string"
   client_id = "your-client-id.apps.googleusercontent.com"
   client_secret = "your-client-secret"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```

3. Restart the app. If this file is missing or misconfigured, the rest of
   the app still works normally — only the Google button shows a friendly
   error instead of crashing.

> ⚠️ Never commit `.streamlit/secrets.toml` — it's already covered by
> `.gitignore`. Only `secrets.toml.example` should be tracked.

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push the repo to GitHub (excluding `users.db`, `.env`, and
   `.streamlit/secrets.toml` as above).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app**
   → select this repo/branch → main file path `app.py`.
3. In the app's **Secrets** settings, paste your `GEMINI_API_KEY` and the
   full `[auth]` block from your local `secrets.toml`.
4. Update the Google Cloud OAuth client's authorized redirect URI to your
   deployed URL (e.g. `https://your-app.streamlit.app/oauth2callback`), and
   update `redirect_uri` in the deployed secrets to match.
5. Deploy. Note: SQLite (`users.db`) does not persist reliably across
   redeploys/sleep on the free tier — fine for a demo, but consider a
   hosted database for real user data.

---

## 📁 Project Structure

```
ToneShift/
│
├── app.py                     # Main Streamlit application (dashboard, rewrite workflow)
├── auth.py                    # Login / signup UI, bcrypt auth, and Google OAuth sync
├── database.py                 # SQLite schema setup (users table)
├── requirements.txt           # Python dependencies (includes streamlit[auth])
├── README.md                   # Project documentation (this file)
├── .env.example                 # Environment variable template (Gemini API key)
├── secrets.toml.example         # Template for .streamlit/secrets.toml (Google OAuth)
├── .gitignore
├── LICENSE                      # MIT license
├── users.db                     # SQLite user database (gitignored, auto-created)
│
├── .streamlit/
│   └── secrets.toml              # Real Google OAuth credentials (gitignored, not tracked)
│
├── utils/
│   ├── __init__.py
│   ├── prompts.py                # Gemini prompt-engineering templates
│   ├── rewrite.py                # Core rewriting logic (Gemini API calls)
│   ├── similarity.py             # Meaning-preservation / drift scoring
│   ├── pdf_export.py             # PDF export utilities (fpdf2)
│   └── helpers.py                # Stats, diff highlighting, history management
│
├── assets/
│   └── logo.png                  # App logo
│
├── styles/
│   ├── style.css                  # Dashboard theme (light & dark mode variables)
│   └── login.css                  # Auth screen theme (glassmorphic console look)
```

---

## 🧭 Future Improvements

- [ ] Multi-language support (rewrite into non-English tones/audiences).
- [ ] Persistent, database-backed rewrite history (currently session-only).
- [ ] Batch rewriting for multiple documents at once.
- [ ] Browser extension for in-place rewriting on any webpage.
- [ ] Support for additional LLM providers (OpenAI, Claude, local models).
- [ ] A/B tone comparison view (rewrite the same text into 2 tones at once).
- [ ] Voice input and text-to-speech playback of the rewritten output.
- [ ] Password reset / account recovery flow.
- [ ] Additional OAuth providers (GitHub, Microsoft).
- [ ] Migrate from SQLite to a hosted database for persistent deployment.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">Built as a demonstration of applied AI engineering — prompt design, meaning verification, secure authentication (including OAuth), and full-stack delivery in one cohesive tool.</p>