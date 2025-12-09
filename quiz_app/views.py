from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

import google.generativeai as genai
import json
import logging
import re

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def create_prompt(topic, num_ques, difficulty):
    """Create the prompt for Gemini."""
    return (
        f"Generate exactly {num_ques} multiple-choice questions about \"{topic}\" "
        f"at {difficulty} difficulty. Return only a single valid JSON object with this shape:\n\n"
        '{\n'
        '  "quiz": [\n'
        '    {\n'
        '      "question": "Question text",\n'
        '      "options": ["opt1", "opt2", "opt3", "opt4"],\n'
        '      "correct_answer": "opt1"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Rules:\n"
        "- Exactly the requested number of questions.\n"
        "- Exactly 4 unique options.\n"
        "- correct_answer must be one of the options.\n"
        "Return ONLY the JSON object."
    )


def extract_json_object(s: str) -> str:
    """Extract the first JSON object found between { ... }"""
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found")
    return s[start:end + 1]


@csrf_exempt
def generate_quiz(request):

    if request.method == "GET":
        # Allow GET for params testing
        topic = request.GET.get("topic", "").strip()
        num_ques = request.GET.get("num_ques", "5").strip()
        difficulty = request.GET.get("difficulty", "medium").strip()

        return JsonResponse({
            "status": "ready",
            "message": "Use POST with JSON, form-data, or URL params.",
            "params_received": {
                "topic": topic,
                "num_ques": num_ques,
                "difficulty": difficulty,
            }
        })

    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    try:
        topic = ""
        num_ques = ""
        difficulty = ""

        # ---------------------------------------------
        # 1. Read body if application/json
        # ---------------------------------------------
        content_type = request.content_type or ""
        if "application/json" in content_type:
            try:
                payload = json.loads(request.body.decode("utf-8") or "{}")
                topic = str(payload.get("topic", "")).strip()
                num_ques = str(payload.get("num_ques", "")).strip()
                difficulty = str(payload.get("difficulty", "")).strip()
            except Exception as e:
                logger.error("Invalid JSON body: %s", e)

        # ---------------------------------------------
        # 2. Read form-data (POST form)
        # ---------------------------------------------
        if not topic:
            topic = (request.POST.get("topic") or "").strip()
        if not num_ques:
            num_ques = (request.POST.get("num_ques") or "").strip()
        if not difficulty:
            difficulty = (request.POST.get("difficulty") or "").strip()

        # ---------------------------------------------
        # 3. Read URL Params (GET-style params)
        # ---------------------------------------------
        if not topic:
            topic = request.GET.get("topic", "").strip()
        if not num_ques:
            num_ques = request.GET.get("num_ques", "").strip()
        if not difficulty:
            difficulty = request.GET.get("difficulty", "").strip()

        # Fallback defaults
        topic = topic or "General Knowledge"
        num_ques = num_ques or "5"
        difficulty = difficulty or "medium"

        logger.warning("💡 Parsed inputs → topic=%r num_ques=%r difficulty=%r",
                       topic, num_ques, difficulty)

        # Validate num_ques
        try:
            num_ques_int = int(num_ques)
        except:
            return HttpResponse("num_ques must be an integer", status=400)

        # ---------------------------------------------
        # Build prompt & call Gemini
        # ---------------------------------------------
        prompt = create_prompt(topic, num_ques_int, difficulty)
        logger.warning("📨 PROMPT SENT TO GEMINI:\n%s", prompt)

        model_name = "gemini-2.5-flash"  # your working model
        model = genai.GenerativeModel(model_name)

        g_response = model.generate_content(prompt)

        raw = getattr(g_response, "text", None) or str(g_response)
        cleaned = raw.strip()

        # Remove ```json fences
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = re.sub(r"^\s*json", "", cleaned, flags=re.IGNORECASE).strip()

        try:
            json_str = extract_json_object(cleaned)
        except Exception:
            logger.error("❌ Could not extract JSON from Gemini\nRaw: %s", cleaned)
            return HttpResponse("Gemini returned non-JSON content", status=502)

        try:
            quiz_json = json.loads(json_str)
        except Exception as e:
            logger.error("❌ JSON parse error: %s\nExtracted: %s", e, json_str)
            return HttpResponse("Invalid JSON from Gemini", status=502)

        return JsonResponse(quiz_json, safe=False)

    except Exception as e:
        logger.exception("❌ Server error")
        return HttpResponse(f"Server error: {str(e)}", status=500)
