from django.conf import settings
from django.http import HttpResponse, JsonResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from google import genai
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

import json
import logging
import re

logger = logging.getLogger(__name__)


# -----------------------------
# Gemini client
# -----------------------------
if settings.GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
else:
    gemini_client = None


# -----------------------------
# Helper: auth-safe API check
# -----------------------------
def require_auth_json(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "AUTH_REQUIRED"},
            status=401
        )
    return None


# -----------------------------
# Prompt builder
# -----------------------------
def create_prompt(topic: str, num_ques: int, difficulty: str) -> str:
    return (
        f"Generate exactly {num_ques} multiple-choice questions about \"{topic}\" "
        f"at {difficulty} difficulty.\n\n"
        "Return ONLY one valid JSON object in the following format:\n\n"
        "{\n"
        '  "quiz": [\n'
        "    {\n"
        '      "question": "Question text",\n'
        '      "options": ["opt1", "opt2", "opt3", "opt4"],\n'
        '      "correct_answer": "opt1"\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )


def extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found")
    return text[start:end + 1]


# -----------------------------
# Generate Quiz API
# -----------------------------
def generate_quiz(request):
    auth_error = require_auth_json(request)
    if auth_error:
        return auth_error

    if gemini_client is None:
        return HttpResponse("Gemini API key not configured", status=500)

    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        topic = payload.get("topic", "General Knowledge")
        num_ques = int(payload.get("num_ques", 5))
        difficulty = payload.get("difficulty", "medium")

        prompt = create_prompt(topic, num_ques, difficulty)

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw = response.text or ""
        raw = raw.strip("`")
        raw = re.sub(r"^\s*json", "", raw, flags=re.I)

        quiz_data = json.loads(extract_json_object(raw))

        return JsonResponse(quiz_data)

    except Exception as e:
        logger.exception("Quiz generation failed")
        return HttpResponse("Server error", status=500)


# -----------------------------
# Download PDF API
# -----------------------------
def download_quiz_pdf(request):
    auth_error = require_auth_json(request)
    if auth_error:
        return auth_error

    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        quiz = payload.get("quiz", [])
        topic = payload.get("topic", "Quiz")

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, f"Quiz Topic: {topic}")
        y -= 40

        pdf.setFont("Helvetica", 11)
        for i, q in enumerate(quiz, 1):
            pdf.drawString(50, y, f"Q{i}. {q['question']}")
            y -= 20
            for j, opt in enumerate(q["options"]):
                pdf.drawString(70, y, f"{chr(65+j)}. {opt}")
                y -= 15
            y -= 20

        pdf.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=quiz.pdf"
        return response

    except Exception:
        return HttpResponse("PDF error", status=500)


# -----------------------------
# Signup view
# -----------------------------
def signup(request):
    next_url = request.GET.get("next", "/")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"/accounts/login/?next={next_url}")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {
        "form": form,
        "next": next_url
    })