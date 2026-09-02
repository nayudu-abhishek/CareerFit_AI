from flask import Flask, request, jsonify, render_template
import os
import json
import re
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader
import docx

load_dotenv()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Configure Gemini API ---
api_key = os.environ.get("GEMINI_API_KEY")
client = None
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in .env — AI analysis will fall back to local scoring.")
else:
    client = genai.Client(api_key=api_key)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

MODEL_NAME = "gemini-3.6-flash"

# ---------- Helpers ----------

def clean_json_string(json_str):
    """Strip markdown code fences Gemini sometimes wraps JSON in."""
    json_str = re.sub(r"```json\s*", "", json_str)
    json_str = re.sub(r"```\s*", "", json_str)
    return json_str.strip()


def local_fallback_analysis(resume_text, jd_text):
    """Naive keyword-overlap analysis used when the AI call fails or no key is set."""

    def get_words(text):
        return set(w.lower() for w in re.findall(r"\b\w{4,}\b", text))

    r_words = get_words(resume_text)
    j_words = get_words(jd_text)

    common = r_words.intersection(j_words)
    missing = j_words.difference(r_words)

    if j_words:
        match_ratio = len(common) / len(j_words)
        score = int(min(match_ratio * 100 * 1.5, 95))
    else:
        score = 10

    return {
        "totalScore": score,
        "matchedKeywords": list(common)[:10],
        "missingKeywords": list(missing)[:10],
        "impactScore": min(score + 10, 90),
        "actionVerbsFound": ["Managed", "Created", "Led"] if score > 50 else ["Worked", "Made"],
        "suggestions": [
            f"Consider adding missing keywords like: {', '.join(list(missing)[:3])}",
            "Quantify your achievements with numbers (e.g., 'Increased revenue by 20%').",
            "Ensure your contact information is clearly visible.",
        ],
    }


def analyze_with_ai(resume_text, jd_text):
    if client is None:
        return local_fallback_analysis(resume_text, jd_text)

    prompt = f"""
    You are an ATS (Applicant Tracking System) Expert.
    Analyze the provided Resume against the Job Description.

    Resume:
    {resume_text}

    Job Description:
    {jd_text}

    Return a valid JSON object with the following structure (do not add any markdown formatting):
    {{
      "totalScore": <integer 0-100>,
      "matchedKeywords": [<list of strings (keywords found in both)>],
      "missingKeywords": [<list of strings (keywords in JD but not Resume)>],
      "impactScore": <integer 0-100 (based on action verbs and impact)>,
      "actionVerbsFound": [<list of strings (action verbs found)>],
      "suggestions": [<list of strings (3-4 specific improvement suggestions)>]
    }}
    """
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        cleaned_json = clean_json_string(response.text)
        return json.loads(cleaned_json)
    except Exception as e:
        print(f"AI JSON Error: {e}")
        return local_fallback_analysis(resume_text, jd_text)


def extract_text_from_file(filepath):
    """Pull plain text out of an uploaded .pdf, .docx, or .txt file."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".pdf":
            reader = PdfReader(filepath)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == ".docx":
            doc = docx.Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        elif ext in (".txt", ".md"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            return ""
    except Exception as e:
        print(f"File extraction error ({filepath}): {e}")
        return ""


def perform_technical_checks(resume_text):
    checks = []

    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text):
        checks.append({"name": "Email Address Detected", "status": "pass", "msg": "Contact info found."})
    else:
        checks.append({"name": "Email Address Detected", "status": "fail", "msg": "Missing email address."})

    if re.search(r"(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", resume_text):
        checks.append({"name": "Phone Number Detected", "status": "pass", "msg": "Phone number found."})
    else:
        checks.append({"name": "Phone Number Detected", "status": "fail", "msg": "Missing phone number."})

    word_count = len(resume_text.split())
    if 400 <= word_count <= 1200:
        checks.append({"name": "Word Count", "status": "pass", "msg": f"Great length ({word_count} words)."})
    else:
        checks.append({
            "name": "Word Count",
            "status": "warn",
            "msg": f"Word count ({word_count}) could be optimized (aim for 400-1200).",
        })

    sections = ["experience", "education", "skills"]
    lower_text = resume_text.lower()
    found = [s for s in sections if s in lower_text]
    if len(found) == len(sections):
        checks.append({"name": "Standard Sections", "status": "pass", "msg": "All standard sections found."})
    else:
        missing = [s for s in sections if s not in found]
        checks.append({
            "name": "Standard Sections",
            "status": "warn",
            "msg": f"Missing sections: {', '.join(missing)}",
        })

    return checks


# ---------- Routes ----------

@app.route("/")
def home():
    return render_template("app.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if request.is_json:
        data = request.json
        resume_text = data.get("resume_text", "")
        jd_text = data.get("job_description", "")
    else:
        resume_text = request.form.get("resume_text", "")
        jd_text = request.form.get("job_description", "")

        if "resume_file" in request.files:
            file = request.files["resume_file"]
            if file.filename:
                saved_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(saved_path)
                if not resume_text:
                    resume_text = extract_text_from_file(saved_path)

        if "jd_file" in request.files:
            file = request.files["jd_file"]
            if file.filename:
                saved_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(saved_path)
                if not jd_text:
                    jd_text = extract_text_from_file(saved_path)

    if not resume_text or not jd_text:
        return jsonify({
            "error": "Missing text content. Could not extract readable text — "
                     "try pasting it directly, or upload a .pdf, .docx, or .txt file."
        }), 400

    ai_results = analyze_with_ai(resume_text, jd_text)
    technical_checks = perform_technical_checks(resume_text)

    response_data = {**ai_results, "checks": technical_checks}
    return jsonify(response_data)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    message = data.get("message")
    resume_text = data.get("resume_text", "")
    jd_text = data.get("jd_text", "")

    if not message:
        return jsonify({"reply": "I didn't catch that. Could you repeat?"})

    if client is None:
        return jsonify({"reply": "AI chat is unavailable: no GEMINI_API_KEY is configured on the server."})

    system_instruction = """
    You are an elite Career Coach and Senior Technical Recruiter with experience at top MNCs (FAANG/MAANG).
    Your goal is to help the candidate optimize their resume to get past ATS systems and ace interviews.

    Context:
    - You have access to the candidate's Resume and the Job Description they are applying for.
    - Be direct, professional, and actionable.
    - Focus on "Impact", "Metrics", and "Keywords".
    - If the user asks for specific advice, give examples of how to rewrite bullet points.
    - Do not be generic. Provide specific keywords to add based on the JD.
    """

    prompt = f"""
    {system_instruction}

    RESUME CONTENT:
    {resume_text[:4000]}... (truncated if too long)

    JOB DESCRIPTION:
    {jd_text[:4000]}... (truncated if too long)

    USER QUESTION:
    {message}
    """

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        reply = response.text
    except Exception as e:
        print(f"Chat Error: {e}")
        reply = "Sorry, I hit an error talking to the AI service. Please try again in a moment."

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, port=8080)