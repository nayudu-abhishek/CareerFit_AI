# Resume ATS Analyzer

Flask app that scores a resume against a job description using Gemini, with a
fallback local keyword-overlap analyzer if no API key is configured, plus a
chat-based AI career coach.

## Project structure

```
resume_ats/
├── app.py                  # Flask backend (routes: /, /analyze, /chat)
├── requirements.txt
├── .env.example            # copy to .env and fill in your key
├── templates/
│   └── app.html            # page markup
├── static/
│   ├── css/
│   │   └── style.css       # all styling
│   └── js/
│       └── app.js          # frontend logic (fetch calls, DOM rendering)
└── uploads/                # uploaded resume/JD files land here
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste in a fresh GEMINI_API_KEY
# get one at https://aistudio.google.com/app/apikey

python app.py
```

Visit http://localhost:8080

## Security note

⚠️ The original version of this project had a Gemini API key hardcoded
directly in `app.py` and committed in a `.env` file. **That key must be
revoked/regenerated** in Google AI Studio — anything shared in a file,
chat, or repo should be treated as burned. This version reads the key only
from the environment via `python-dotenv`, and `.env` is git-ignored.

## What changed from the original

- Removed the hardcoded API key; `app.py` now reads `GEMINI_API_KEY` from
  the environment only.
- Split the previously-missing `app.html` template into separate
  `templates/app.html`, `static/css/style.css`, and `static/js/app.js`.
- `/chat` now returns a clean error message instead of leaking exception
  text (and the raw API key context) to the client.
- Added `.gitignore`, `requirements.txt`, and `.env.example`.
