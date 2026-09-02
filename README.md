# CareerFit AI

A Flask web app that scores your resume against a job description — like an
Applicant Tracking System (ATS) would — using Google's Gemini AI, with a
built-in fallback scorer if no AI key is configured. Includes an AI career
coach chat to help you improve specific bullet points.

---

## What it does

1. You paste or upload a resume and a job description.
2. CareerFit AI sends both to Gemini, which returns:
   - An overall ATS match score
   - Matched and missing keywords
   - An "impact" score based on strong action verbs
   - Specific improvement suggestions
3. It also runs simple technical checks (email found? phone number found?
   word count in a good range? standard sections present?).
4. You can then chat with an AI career coach about how to improve things.

---

## Project structure

careerfit-ai/
├── app.py # Flask backend — all routes and AI logic
├── requirements.txt # Python packages needed
├── .env.example # Template for your API key — copy this to .env
├── .gitignore
├── README.md
├── templates/
│ └── app.html # Page layout (HTML)
├── static/
│ ├── css/
│ │ └── style.css # All styling
│ └── js/
│ └── app.js # Frontend logic — talks to the Flask backend
└── uploads/ # Uploaded resume/JD files are saved here temporarily


---

## Setup (first time only)

**1. Open a terminal in the project folder**

**2. Create and activate a virtual environment**

```bash
python -m venv .venv
```

- Windows: `.venv\Scripts\activate`
- Mac/Linux: `source .venv/bin/activate`

You'll know it worked when you see `(.venv)` at the start of your terminal
prompt.

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your Gemini API key**

- Copy `.env.example` to a new file named exactly `.env` (not `.env.example`
  — Flask only reads the real `.env`)
- Get a free key at https://aistudio.google.com/app/apikey
- Paste it in like this:

GEMINI_API_KEY=your-key-here


⚠️ Never share this key or commit it to GitHub. If it's ever exposed
(pasted in a chat, screenshot, public repo, etc.), regenerate it immediately.

---

## Running the app

```bash
python app.py
```

You should see:

Running on http://127.0.0.1:8080