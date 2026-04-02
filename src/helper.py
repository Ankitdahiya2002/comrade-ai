# =============================================================
# src/helper.py
# AI engine — Claude (primary) + Gemini (fallback).
#
# Priority order:
#   1. Claude Sonnet 4  — if ANTHROPIC_API_KEY is in secrets
#   2. Gemini 2.5 Flash — if GEMINI_API_KEY is in secrets
#   3. Error message    — if neither key is set
#
# Also handles:
#   - File context injection (AI reads uploaded file)
#   - Image generation via Stability AI
#   - Trending prompt recommendations
# =============================================================

import re
import requests
import base64
from datetime import date

import streamlit as st

# ── Read API keys from secrets (never hardcode them) ──────────
ANTHROPIC_KEY  = st.secrets.get("ANTHROPIC_API_KEY", "")
GEMINI_KEY     = st.secrets.get("GEMINI_API_KEY", "")
STABILITY_KEY  = st.secrets.get("STABILITY_API_KEY", "")

# ── Initialise Gemini SDK only if the key exists ──────────────
_genai = None
if GEMINI_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        _genai = genai
    except Exception as e:
        print(f"Gemini init failed: {e}")

# Max characters of file text sent to the AI per message
MAX_FILE_CHARS = 12_000


# =============================================================
# MAIN CHAT FUNCTION — called by app.py
# =============================================================

def ai_chat_response(
    prompt: str,
    model_choice: str = "claude",
    file_contexts: list[dict] = None,
) -> str:
    """
    Send a prompt to the selected AI model and return the response.

    Parameters
    ----------
    prompt        : Conversation history + current user message.
    model_choice  : "claude" or "gemini". Claude is always tried first
                    unless the user explicitly switches to Gemini.
    file_contexts : List of {"name": str, "text": str} dicts.
                    If provided, the file text is prepended to the prompt
                    so the AI can answer questions about the file.

    Returns
    -------
    str : The AI's response text.
    """
    # Build the full prompt (file context + conversation)
    full_prompt = _build_prompt(prompt, file_contexts or [])

    # Route to the correct model
    if model_choice == "gemini":
        return _call_gemini(full_prompt)

    # Claude is the default — try it first
    if ANTHROPIC_KEY:
        result = _call_claude(full_prompt)
        if not result.startswith("⚠️"):
            return result
        # Claude failed → fall back to Gemini automatically
        print("Claude call failed, falling back to Gemini.")

    # Gemini fallback
    if GEMINI_KEY:
        return _call_gemini(full_prompt)

    return (
        "⚠️ No AI model is configured. "
        "Please add ANTHROPIC_API_KEY or GEMINI_API_KEY to your .streamlit/secrets.toml."
    )


# =============================================================
# PRIVATE — Claude and Gemini callers
# =============================================================

def _call_claude(prompt: str) -> str:
    """Call Claude Sonnet 4 via the Anthropic REST API."""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        return f"⚠️ Claude API error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"⚠️ Claude request failed: {e}"


def _call_gemini(prompt: str) -> str:
    """Call Gemini 2.5 Flash via the google-generativeai SDK."""
    if not _genai:
        return "⚠️ Gemini is not configured. Add GEMINI_API_KEY to secrets."
    try:
        model    = _genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content({"parts": [{"text": prompt}]})
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini error: {e}"


def _build_prompt(prompt: str, file_contexts: list[dict]) -> str:
    """
    Prepend any uploaded file content to the prompt.
    The AI will see the file text before the conversation,
    so it can answer questions about the file accurately.
    """
    if not file_contexts:
        return prompt

    parts = [
        "The user has uploaded the following file(s).\n"
        "Use this content to answer their questions accurately.\n"
    ]
    for fc in file_contexts:
        text = fc.get("text", "").strip()
        # Truncate very long files to stay within token limits
        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + "\n[... file truncated ...]"
        parts.append(f"--- FILE: {fc.get('name', 'file')} ---\n{text}\n--- END ---")

    parts.append("Answer based on the file content above.\n")
    parts.append(prompt)
    return "\n\n".join(parts)


# =============================================================
# IMAGE GENERATION
# =============================================================

# Regex that detects image-creation requests in user messages
_IMAGE_REGEX = re.compile(
    r"\b(create|generate|make|draw|design|paint|render|convert|turn|change)\b"
    r".{0,30}"
    r"\b(image|photo|picture|illustration|art|avatar|ghibli|anime|cartoon|"
    r"sketch|poster|wallpaper|portrait)\b",
    re.IGNORECASE,
)

# Style keywords → Stability AI prompt suffixes
_STYLE_MAP = {
    "ghibli":    "Studio Ghibli anime style, hand-painted, warm colours, Miyazaki",
    "anime":     "Japanese anime style, vibrant colours, sharp lines",
    "cartoon":   "cartoon illustration, bold outlines, flat colours",
    "sketch":    "pencil sketch, black and white, hand-drawn",
    "realistic": "photorealistic, 8K, cinematic lighting, detailed",
    "pixel":     "pixel art, 16-bit, retro game aesthetic",
    "poster":    "vintage poster design, bold typography, flat colours",
}


def is_image_request(text: str) -> bool:
    """Return True if the user's message is asking to create an image."""
    return bool(_IMAGE_REGEX.search(text))


def generate_image(prompt: str) -> dict:
    """
    Generate an image via Stability AI.
    Auto-detects style keywords and enhances the prompt.

    Returns a dict:
        success      : bool
        image_b64    : base64-encoded PNG string (or None)
        revised_prompt: the enhanced prompt that was sent
        error        : error message (or None)
    """
    # Detect and append a style suffix
    style_suffix = ""
    low = prompt.lower()
    for keyword, style in _STYLE_MAP.items():
        if keyword in low:
            style_suffix = f", {style}"
            break

    enhanced = prompt + style_suffix + ", high quality, detailed"

    # No Stability key — return the enhanced prompt for other tools
    if not STABILITY_KEY:
        return {
            "success":       False,
            "image_b64":     None,
            "revised_prompt": enhanced,
            "error":         "no_key",
        }

    try:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={
                "authorization": f"Bearer {STABILITY_KEY}",
                "accept":        "image/*",
            },
            files={"none": ""},
            data={
                "prompt":        enhanced,
                "output_format": "png",
                "width":         1024,
                "height":        1024,
            },
            timeout=60,
        )
        if response.status_code == 200:
            b64 = base64.b64encode(response.content).decode()
            return {"success": True, "image_b64": b64,
                    "revised_prompt": enhanced, "error": None}
        return {
            "success":       False,
            "image_b64":     None,
            "revised_prompt": enhanced,
            "error":         f"Stability API {response.status_code}",
        }
    except Exception as e:
        return {"success": False, "image_b64": None,
                "revised_prompt": enhanced, "error": str(e)}


# =============================================================
# TRENDING RECOMMENDATIONS
# =============================================================

# 18 curated prompts — rotated daily so the list feels fresh
_TRENDING = [
    "Explain how neural networks learn",
    "Write a Python function to sort a list of dictionaries",
    "Create a Ghibli-style image of a forest at sunset",
    "Summarise my uploaded file in bullet points",
    "What are the best Python libraries in 2026?",
    "Write a professional LinkedIn post about my project",
    "Help me prepare for a technical interview",
    "Explain the difference between SQL and NoSQL",
    "Create a 7-day study plan for data structures",
    "Generate a pixel art avatar of a robot",
    "Draft a project proposal for an AI application",
    "Explain time complexity with simple examples",
    "What is the difference between Claude and Gemini?",
    "Write a short story about an AI assistant",
    "Give me 10 MCQ questions on machine learning",
    "Analyse my uploaded Excel file and find key trends",
    "Design a motivational poster for productivity",
    "Explain REST APIs to a beginner",
]


def get_trending(count: int = 4) -> list[str]:
    """
    Return `count` trending prompts.
    Rotates the list daily using the date as a seed.
    """
    seed   = hash(str(date.today())) % len(_TRENDING)
    rotated = _TRENDING[seed:] + _TRENDING[:seed]
    return rotated[:count]
