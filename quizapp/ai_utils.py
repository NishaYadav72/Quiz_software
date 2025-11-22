import os
import json
import re
from PyPDF2 import PdfReader
from PIL import Image
from openai import OpenAI

# -----------------------------
# OpenAI client setup
# -----------------------------
API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None
OPENAI_AVAILABLE = client is not None

DEFAULT_MODEL = "gpt-4o-mini"


# -----------------------------
# JSON Extraction Helper
# -----------------------------
def _extract_json_from_text(s: str):
    if not s:
        return None

    s = s.strip()

    # Try extracting JSON array
    match = re.search(r"\[\s*{.*}\s*\]", s, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    # Try whole text
    try:
        return json.loads(s)
    except:
        return None


# -----------------------------
# Fallback MCQs (with explanations)
# -----------------------------
def _dummy_mcq_questions(n=10):
    out = []
    for i in range(n):
        out.append({
            "question": f"Sample Question {i+1} (fallback)",
            "options": [
                f"Option A{i+1}",
                f"Option B{i+1}",
                f"Option C{i+1}",
                f"Option D{i+1}"
            ],
            "answer": f"Option A{i+1}",
            "explanation": f"This is the explanation for Sample Question {i+1}."
        })
    return out


# -----------------------------
# Generate MCQs with Explanation
# -----------------------------
def generate_text_questions(text: str, num_questions: int = 10):

    if not OPENAI_AVAILABLE:
        print("⚠️ OpenAI not available — fallback used.")
        return _dummy_mcq_questions(num_questions)

    prompt = f"""
Generate exactly {num_questions} multiple-choice questions from the text below.

Return STRICTLY a JSON array ONLY, with each item containing these keys:
  - "question": string
  - "options": array of 4 strings
  - "answer": one of the options (exact string)
  - "explanation": short explanation (1–2 sentences)

Format example:
[
  {{
    "question": "What is Python?",
    "options": ["A snake", "A programming language", "A car", "A movie"],
    "answer": "A programming language",
    "explanation": "Python is a high-level programming language."
  }}
]

Rules:
- EXACTLY 4 options.
- "answer" MUST match exactly one option.
- Explanation must be short (1–2 lines).
- No extra text outside JSON array.

Text:
{text}
"""

    try:
        resp = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000
        )

        raw = resp.choices[0].message.content
        print("RAW DEBUG:", raw[:500])

        parsed = _extract_json_from_text(raw)

        if parsed and isinstance(parsed, list):
            cleaned = []

            for q in parsed:
                try:
                    if not isinstance(q, dict):
                        continue

                    question = q.get("question")
                    options = q.get("options")
                    answer = q.get("answer")
                    explanation = q.get("explanation", "")

                    if not question or not options or len(options) != 4 or not answer:
                        continue

                    # ensure answer is one of the options
                    if answer not in options:
                        # Allow A/B/C/D mapping
                        label_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                        if answer.strip() in label_map:
                            answer = options[label_map[answer.strip()]]
                        else:
                            continue

                    cleaned.append({
                        "question": question,
                        "options": options,
                        "answer": answer,
                        "explanation": explanation if explanation else "No explanation provided."
                    })

                except:
                    continue

            # Correct count handling
            if len(cleaned) >= num_questions:
                return cleaned[:num_questions]

            if 0 < len(cleaned) < num_questions:
                need = num_questions - len(cleaned)
                return cleaned + _dummy_mcq_questions(need)

        print("⚠️ JSON parsing failed → fallback used.")
        return _dummy_mcq_questions(num_questions)

    except Exception as e:
        print("❌ OpenAI Error:", e)
        return _dummy_mcq_questions(num_questions)


# -----------------------------
# PDF Extractor
# -----------------------------
def extract_text_from_pdf(file_path: str):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            content = page.extract_text() or ""
            text += content + "\n"
    except:
        return ""
    return text.strip()


# -----------------------------
# Image OCR Placeholder
# -----------------------------
def extract_text_from_image(image_path: str):
    return "Image OCR not implemented."


# -----------------------------
# Video Text Placeholder
# -----------------------------
def extract_text_from_video(video_path: str):
    return "Video text extraction not implemented."
