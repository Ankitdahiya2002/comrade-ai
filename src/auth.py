# =============================================================
# src/auth.py
# Ultimate High-Fidelity & Fully Functional Auth Module
# =============================================================

import random
import re
import time
import uuid
from datetime import datetime, timedelta

import requests
import streamlit as st

from src.db import (
    create_user,
    get_user,
    upsert_oauth_user,
    update_reset_token,
    verify_user_credentials,
    verify_user_token,
    reset_user_password_by_token,
)
from src.email_utils import send_verification_email, send_reset_email
from src.otp_utils import OTPManager


import os
import json
import base64

# ── Image to Base64 Helper ───────────────────────────────────
def _get_base64_image(img_path):
    if not os.path.exists(img_path): return ""
    with open(img_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ── Load remembered credentials ───────────────────────────────
def _get_remembered():
    f = ".remembered.json"
    if os.path.exists(f):
        try:
            with open(f, "r") as r: return json.load(r)
        except: return {}
    return {}


def _save_remembered(email, pw, remember):
    f = ".remembered.json"
    if remember:
        with open(f, "w") as w: json.dump({"email": email, "pass": pw}, w)
    else:
        if os.path.exists(f): os.remove(f)


# =============================================================
# CSS — Ultra-Compact Premium Design
# =============================================================

def _apply_auth_css(mode="landing", IMG_B64="", BG_B64=""):
    # Aggressive thematic mapping for unique, attractive page identities
    theme_colors = {
        "landing": {"glow": "rgba(59, 130, 246, 0.6)",  "tint": "rgba(59, 130, 246, 0.15)", "primary": "#3b82f6"}, # Blue
        "login":   {"glow": "rgba(168, 85, 247, 0.6)",  "tint": "rgba(168, 85, 247, 0.15)", "primary": "#a855f7"}, # Purple
        "signup":  {"glow": "rgba(16, 185, 129, 0.6)",  "tint": "rgba(16, 185, 129, 0.15)", "primary": "#10b981"}, # Green
        "otp":     {"glow": "rgba(245, 158, 11, 0.6)",  "tint": "rgba(245, 158, 11, 0.15)", "primary": "#f59e0b"}, # Amber
        "forgot":  {"glow": "rgba(239, 68, 68, 0.6)",   "tint": "rgba(239, 68, 68, 0.15)",  "primary": "#ef4444"}, # Red
        "reset":   {"glow": "rgba(244, 114, 182, 0.6)", "tint": "rgba(244, 114, 182, 0.15)", "primary": "#f472b6"}, # Pink
        "success": {"glow": "rgba(6, 182, 212, 0.6)",   "tint": "rgba(6, 182, 212, 0.15)",  "primary": "#06b6d4"}, # Cyan
    }
    theme = theme_colors.get(mode, theme_colors["landing"])
    glow  = theme["glow"]
    tint  = theme["tint"]
    pri   = theme["primary"]

    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Grotesk:wght@300;500;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True
    )
    # Inject Comrade Ai logo as background via base64
    css_template = f"""
<style>
/* ── Background: Dark dotted + per-page colour glow ── */
html, body, [data-testid="stAppViewContainer"] {{
    background-color: #06020f !important;
    background-image:
        radial-gradient(ellipse 90% 70% at 50% 40%, {glow}, transparent 70%),
        radial-gradient(#2a2d36 1px, transparent 1px) !important;
    background-size: cover, 22px 22px !important;
    color: #1f2937 !important;
    font-family: 'Inter', sans-serif !important;
}}

[data-testid="stMainBlockContainer"] {{
    max-width: { "1200px" if st.session_state.get("auth_mode") == "landing" else "500px" } !important;
    margin: 0 auto !important;
    padding: 2rem 0 !important;
}}

/* ── Glassmorphism Research Card ── */
.research-card {{
    background: rgba(10, 10, 20, 0.6) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 24px !important;
    padding: 3rem !important;
    margin-top: 4rem !important;
    margin-bottom: 6rem !important;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4) !important;
}}
.research-card h1, .research-card h2, .research-card h3 {{
    font-family: 'Orbitron', sans-serif !important;
    color: #ffffff !important;
    letter-spacing: 0.05em !important;
}}
.research-card p, .research-card li {{
    color: rgba(255, 255, 255, 0.8) !important;
    line-height: 1.6 !important;
    font-size: 15px !important;
}}
.research-card hr {{
    border-color: rgba(255, 255, 255, 0.1) !important;
}}

@media (max-width: 640px) {{
    [data-testid="stMainBlockContainer"] {{
        max-width: 100% !important;
        padding: 1rem !important;
    }}
}}

/* ── Auth dark card (login, signup, otp pages) ── */
.auth-card {{
    background: #1a1b1e !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 24px !important;
    padding: 2rem 1.75rem 1.75rem !important;
    box-shadow: 0 32px 80px rgba(0,0,0,0.6) !important;
    margin-top: 3vh !important;
    margin-bottom: 3vh !important;
    color: #ffffff !important;
}}

/* ── Auth Typography ── */
.auth-title {{
    font-size: 1.875rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    text-align: center !important;
    margin: 0.5rem 0 0.4rem !important;
}}
.auth-subtitle {{
    font-size: 0.875rem !important;
    color: #9ca3af !important;
    text-align: center !important;
    margin-bottom: 1.5rem !important;
    line-height: 1.5 !important;
}}

/* ── Labels inside card ── */
.auth-card .stTextInput label,
.auth-card .stSelectbox label {{
    color: #374151 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    margin-bottom: 3px !important;
}}

/* ── Inputs inside card ── */
.auth-card .stTextInput > div > div > input,
.auth-card .stSelectbox div[data-baseweb="select"] > div {{
    background: #f9fafb !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #111827 !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
.auth-card .stTextInput > div > div > input:focus {{
    border-color: #1a4fcc !important;
    box-shadow: 0 0 0 3px rgba(26,79,204,0.12) !important;
    background: #fff !important;
}}
.auth-card .stTextInput > div > div > input::placeholder {{
    color: #9ca3af !important;
}}

/* ── Primary blue button ── */
.primary-btn .stButton > button {{
    background: #1a4fcc !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    padding: 12px 20px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    transition: background 0.2s, transform 0.15s, box-shadow 0.2s !important;
    height: auto !important;
}}
.primary-btn .stButton > button:hover {{
    background: #1340a8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(26,79,204,0.28) !important;
}}

/* ── Social outline buttons ── */
.social-btn .stButton > button {{
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    color: #374151 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: background 0.15s, border-color 0.15s !important;
    height: auto !important;
}}
.social-btn .stButton > button:hover {{
    background: #f3f4f6 !important;
    border-color: #d1d5db !important;
}}

/* ── Auth-card scoped button overrides (higher specificity) ── */
.auth-card .primary-btn .stButton > button,
.auth-card .primary-btn [data-testid="stBaseButton-secondary"],
.auth-card .primary-btn [data-testid="stBaseButton-primary"] {{
    background: #1a4fcc !important;
    background-color: #1a4fcc !important;
    border: none !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border-radius: 10px !important;
    padding: 13px 20px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    width: 100% !important;
    box-shadow: 0 4px 14px rgba(26,79,204,0.3) !important;
    cursor: pointer !important;
}}
.auth-card .primary-btn .stButton > button:hover {{
    background: #1340a8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(26,79,204,0.4) !important;
}}
.auth-card .social-btn .stButton > button,
.auth-card .social-btn [data-testid="stBaseButton-secondary"] {{
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1.5px solid #e5e7eb !important;
    color: #374151 !important;
    -webkit-text-fill-color: #374151 !important;
    border-radius: 10px !important;
    padding: 11px 14px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    width: 100% !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}}
.auth-card .social-btn .stButton > button:hover {{
    background: #f9fafb !important;
    border-color: #d1d5db !important;
}}
.auth-card .signup-btn .stButton > button,
.auth-card .signup-btn [data-testid="stBaseButton-secondary"] {{
    background: transparent !important;
    background-color: transparent !important;
    border: 1.5px solid #1a4fcc !important;
    color: #1a4fcc !important;
    -webkit-text-fill-color: #1a4fcc !important;
    border-radius: 10px !important;
    padding: 11px 20px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    width: 100% !important;
}}
.auth-card .signup-btn .stButton > button:hover {{
    background: rgba(26,79,204,0.05) !important;
}}

/* ── Legacy dark inputs (non-card pages) ── */
.stTextInput label {{
    color: #8e8e8e !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    margin-bottom: 1px !important;
}}
.stTextInput > div > div > input {{
    background: #2a2b2f !important;
    border: 1px solid #3a3b3f !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {pri} !important;
    box-shadow: 0 0 0 1px {pri}22 !important;
}}

/* ── Auth-card input overrides (white card = light inputs) ── */
.auth-card .stTextInput label,
.auth-card .stDateInput label,
.auth-card .stSelectbox label {{
    color: #374151 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    margin-bottom: 3px !important;
}}
.auth-card .stTextInput > div > div > input {{
    background: #f9fafb !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
}}
.auth-card .stTextInput > div > div > input:focus {{
    border-color: #1a4fcc !important;
    box-shadow: 0 0 0 3px rgba(26,79,204,0.12) !important;
    background: #ffffff !important;
}}
.auth-card .stTextInput > div > div > input::placeholder {{
    color: #9ca3af !important;
}}
/* Selectbox inside auth-card */
.auth-card .stSelectbox > div > div {{
    background: #f9fafb !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #111827 !important;
}}
/* Forgot password button as a subtle link */
.auth-card .stButton > button[data-testid="stBaseButton-secondary"][aria-label*="Forgot"],
.auth-card [data-testid="stButton"]:has(button:contains("Forgot")) button {{
    background: transparent !important;
    border: none !important;
    color: #1a4fcc !important;
    -webkit-text-fill-color: #1a4fcc !important;
    font-size: 13px !important;
    padding: 4px 0 !important;
    box-shadow: none !important;
    text-decoration: underline !important;
    width: auto !important;
}}

/* ── Legacy Primary Action Button ── */
.primary-btn .stButton > button {{
    background: #1c1d21 !important;
    border: 1px solid #2c2d31 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    padding: 6px 20px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}}
.primary-btn .stButton > button:hover {{
    background: {pri}22 !important;
    border-color: {pri} !important;
}}

/* ── Custom Role Toggles (Screenshot Match) ── */
.role-header {{
    background: #000000 !important;
    color: #ffffff !important;
    text-align: center !important;
    padding: 10px 0 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    border-radius: 4px !important;
    margin-bottom: 12px !important;
    width: 100% !important;
}}
.stRadio > div {{ 
    background: transparent !important;
    display: flex !important;
    justify-content: space-between !important;
    gap: 0 !important;
}}
.stRadio label {{
    flex: 0 1 auto !important;
    min-width: 140px !important;
    background: #000000 !important;
    border: 1px solid #333333 !important;
    border-radius: 50px !important; /* Authentic Pill shape */
    padding: 12px 24px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}}
.stRadio label:hover {{
    border-color: #555555 !important;
}}
.stRadio label:has(input:checked) {{
    background: #111111 !important;
    border: 2px solid #19c37d !important;
    transform: scale(1.02) !important;
}}
.stRadio [data-testid="stWidgetLabel"] {{
    display: none !important;
}}

/* ── Advanced Landing Page Styles (User Provided Design) ── */
.font-futuristic {{
    font-family: 'Orbitron', sans-serif !important;
    letter-spacing: 0.15em !important;
}}

@keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 15px {pri}55, 0 0 30px {pri}33; }}
    50% {{ box-shadow: 0 0 25px {pri}88, 0 0 50px {pri}55; }}
}}

.hero-action .stButton > button {{
    animation: pulse-glow 3s infinite ease-in-out !important;
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
    border: 2px solid rgba(255,255,255,0.25) !important;
    color: #ffffff !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 16px 48px !important;
    border-radius: 50px !important;
    box-shadow: 0 0 25px rgba(124,58,237,0.7), 0 8px 32px rgba(79,70,229,0.4) !important;
    transition: all 0.3s ease !important;
    height: auto !important;
    width: auto !important;
}}

.hero-action .stButton > button:hover {{
    transform: scale(1.06) translateY(-2px) !important;
    filter: brightness(1.15) !important;
    box-shadow: 0 0 40px rgba(124,58,237,0.9), 0 12px 40px rgba(79,70,229,0.5) !important;
    border-color: rgba(255,255,255,0.5) !important;
}}

.stars-overlay {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image: radial-gradient(white, rgba(255,255,255,0.2) 2px, transparent 40px);
    background-size: 550px 550px;
    opacity: 0.15;
    z-index: -1;
}}

.brand-title-hl {{
    font-family: 'Orbitron', sans-serif !important;
    font-size: 80px !important;
    font-weight: 900 !important;
    color: #ffffff;
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.5);
    margin-bottom: 10px !important;
    letter-spacing: 0.15em !important;
}}

.brand-tagline-hl {{
    color: rgba(191, 219, 254, 0.8) !important; /* Blue 200/80 */
    font-size: 18px !important;
    font-weight: 300 !important;
    letter-spacing: 0.2em !important;
    font-style: italic !important;
    text-transform: uppercase !important;
    margin-bottom: 2rem !important;
}}

.btn-text-link div[data-testid="stButton"] button {{
    background: transparent !important;
    background-color: transparent !important;
    border: 1.5px solid rgba(255,255,255,0.35) !important;
    box-shadow: none !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.2em !important;
    padding: 8px 24px !important;
    text-transform: uppercase !important;
    border-radius: 50px !important;
    transition: all 0.3s ease !important;
    width: auto !important;
    margin: 0 auto !important;
    display: block !important;
    min-height: unset !important;
}}

.btn-text-link div[data-testid="stButton"] button:hover {{
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.7) !important;
    transform: scale(1.04) !important;
}}

.btn-text-link div[data-testid="stButton"] {{
    display: flex !important;
    justify-content: center !important;
}}

[data-testid="stSidebar"] {{ display: none !important; }}
#MainMenu, footer, header, [data-testid="stToolbar"] {{ display: none !important; }}
</style>
<div class="stars-overlay"></div>
"""
    st.markdown(css_template, unsafe_allow_html=True)


# =============================================================
# DIALOGS
# =============================================================

@st.dialog("Comrade AI Research Portal", width="large")
def _show_research_dialog():
    """Display the high-fidelity HTML project documentation."""
    import streamlit.components.v1 as components
    if os.path.exists("RESEARCH.md"):
        with open("RESEARCH.md", "r") as f:
            content = f.read()
        components.html(content, height=800, scrolling=True)
    else:
        st.error("Research portal not found.")

def auth_page():
    # Load assets
    img_b64 = _get_base64_image("assets/banner.png")
    bg_b64  = _get_base64_image("assets/background.png")
    
    # Apply dynamic CSS based on the current mode
    _apply_auth_css(st.session_state.get("auth_mode", "landing"), img_b64, bg_b64)
    
    # ── Session defaults (Inside function for robustness) ─────────
    rem = _get_remembered()
    for key, default in [
        ("auth_mode",    "landing"),
        ("auth_role",    "user"),
        ("prefill_email", rem.get("email", "")),
        ("prefill_pass",  rem.get("pass", "")),
        ("otp_phone",    ""),
        ("otp_sent",     False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default
    
    # Callback handles
    access_token = st.query_params.get("access_token")
    if access_token:
        _handle_google_callback(access_token[0] if isinstance(access_token, list) else access_token)
        return

    pages = {
        "landing":   _landing_page,
        "login":     _login_page,
        "signup":    _signup_page,
        "otp":       _otp_page,
        "forgot":    _forgot_page,
        "reset":     _reset_page,
        "success":   _success_page,
    }
    pages.get(st.session_state.auth_mode, _landing_page)()

    # ── Force-apply button colours via JS (CSS alone can't beat Streamlit) ──
    import streamlit.components.v1 as components
    components.html("""
<script>
(function styleAuthButtons() {
    const doc = window.parent.document;

    // Button style map: text → { bg, color, border, borderRadius, hoverBg }
    const STYLES = {
        "CONTINUE": {
            bg: "linear-gradient(90deg, #1565c0 0%, #42a5f5 100%)", color: "#fff", border: "none",
            shadow: "0 4px 20px rgba(21,101,192,0.4)", radius: "12px",
            hoverBg: "linear-gradient(90deg, #1976d2 0%, #64b5f6 100%)"
        },
        "OTP-BASED LOGIN": {
            bg: "#16171b", color: "#ffffff", border: "1px solid rgba(255,255,255,0.1)",
            shadow: "none", radius: "12px",
            hoverBg: "#2a2b30"
        },
        "SIGN IN WITH GOOGLE": {
            bg: "#16171b", color: "#ffffff", border: "1px solid rgba(255,255,255,0.1)",
            shadow: "none", radius: "12px",
            hoverBg: "#2a2b30"
        },
        "SIGN UP": {
            bg: "transparent", color: "#8da4ec", border: "none",
            shadow: "none", radius: "4px",
            hoverBg: "transparent"
        },
        "FORGOT PASSWORD?": {
            bg: "transparent", color: "#8da4ec", border: "none",
            shadow: "none", radius: "4px",
            hoverBg: "transparent"
        },
        "SEND LINK": {
            bg: "linear-gradient(90deg, #1565c0 0%, #42a5f5 100%)", color: "#fff", border: "none",
            shadow: "0 4px 14px rgba(26,79,204,0.35)", radius: "12px",
            hoverBg: "linear-gradient(90deg, #1976d2 0%, #64b5f6 100%)"
        },
        "BACK": {
            bg: "transparent", color: "#ffffff", border: "1.5px solid rgba(255,255,255,0.4)",
            shadow: "none", radius: "12px",
            hoverBg: "rgba(255,255,255,0.1)"
        },
        "SEND CODE": {
            bg: "linear-gradient(90deg, #1565c0 0%, #42a5f5 100%)", color: "#fff", border: "none",
            shadow: "0 4px 14px rgba(26,79,204,0.35)", radius: "12px",
            hoverBg: "linear-gradient(90deg, #1976d2 0%, #64b5f6 100%)"
        },
        "VERIFY": {
            bg: "#19c37d", color: "#fff", border: "none",
            shadow: "0 4px 14px rgba(25,195,125,0.35)", radius: "12px",
            hoverBg: "#0fa86a"
        },
        "CREATE ACCOUNT": {
            bg: "linear-gradient(90deg, #1565c0 0%, #42a5f5 100%)", color: "#fff", border: "none",
            shadow: "0 4px 14px rgba(26,79,204,0.35)", radius: "12px",
            hoverBg: "linear-gradient(90deg, #1976d2 0%, #64b5f6 100%)"
        },
        "SIGN IN INSTEAD": {
            bg: "transparent", color: "#8da4ec", border: "none",
            shadow: "none", radius: "10px",
            hoverBg: "rgba(26,79,204,0.05)"
        },
    };

    doc.querySelectorAll("button").forEach(btn => {
        const txt = btn.textContent.trim().toUpperCase().replace(/\\s+/g, ' ');
        let s = null;
        for (const [key, val] of Object.entries(STYLES)) {
            if (txt.includes(key)) { s = val; break; }
        }
        if (!s) return;

        btn.style.cssText = [
            `background: ${s.bg} !important`,
            `background-color: ${s.bg.includes('gradient') ? 'transparent' : s.bg} !important`,
            `color: ${s.color} !important`,
            `-webkit-text-fill-color: ${s.color} !important`,
            `border: ${s.border} !important`,
            `box-shadow: ${s.shadow} !important`,
            `border-radius: ${s.radius} !important`,
            `font-size: 14px !important`,
            `font-weight: ${s.bg === 'transparent' ? '700' : '600'} !important`,
            `padding: ${s.bg === 'transparent' ? '0' : '11px 16px'} !important`,
            `width: ${s.bg === 'transparent' ? 'auto' : '100%'} !important`,
            `cursor: pointer !important`,
            `transition: all 0.2s ease !important`,
        ].join('; ');

        // Force inner elements (like paragraphs) to inherit the color
        btn.querySelectorAll('*').forEach(child => {
            if (child.tagName === 'P' || child.tagName === 'SPAN' || child.tagName === 'DIV') {
                child.style.color = s.color + ' !important';
                child.style.webkitTextFillColor = s.color + ' !important';
            }
        });

        btn.onmouseenter = () => { btn.style.background = s.hoverBg; btn.style.transform = s.bg === 'transparent' ? 'translateY(0)' : 'translateY(-1px)'; };
        btn.onmouseleave = () => { btn.style.background = s.bg; btn.style.transform = 'translateY(0)'; };
    });
})();

// Re-run after short delays
setTimeout(() => { /* ... */ (function styleAuthButtons() {
    const doc = window.parent.document;
    const STYLES = {"CONTINUE":{bg:"linear-gradient(90deg, #1565c0 0%, #42a5f5 100%)",color:"#fff",border:"none",shadow:"0 4px 20px rgba(21,101,192,0.4)",radius:"12px",hoverBg:"linear-gradient(90deg, #1976d2 0%, #64b5f6 100%)"},"OTP-BASED LOGIN":{bg:"#16171b",color:"#ffffff",border:"1px solid rgba(255,255,255,0.1)",shadow:"none",radius:"12px",hoverBg:"#2a2b30"},"SIGN IN WITH GOOGLE":{bg:"#16171b",color:"#ffffff",border:"1px solid rgba(255,255,255,0.1)",shadow:"none",radius:"12px",hoverBg:"#2a2b30"},"SIGN UP":{bg:"transparent",color:"#8da4ec",border:"none",shadow:"none",radius:"4px",hoverBg:"transparent"},"FORGOT PASSWORD?":{bg:"transparent",color:"#8da4ec",border:"none",shadow:"none",radius:"4px",hoverBg:"transparent"}};
    doc.querySelectorAll("button").forEach(btn => { 
        const txt = btn.textContent.trim().toUpperCase().replace(/\\s+/g,' ');
        let s = null; for (const [k, v] of Object.entries(STYLES)) { if(txt.includes(k)){ s=v; break; } }
        if(!s) return; 
        btn.style.cssText=`background:${s.bg}!important;color:${s.color}!important;-webkit-text-fill-color:${s.color}!important;border:${s.border}!important;box-shadow:${s.shadow}!important;border-radius:${s.radius}!important;font-size:14px!important;font-weight:${s.bg==='transparent'?'700':'600'}!important;padding:${s.bg==='transparent'?'0':'11px 16px'}!important;width:${s.bg==='transparent'?'auto':'100%'}!important;cursor:pointer!important;`; 
        btn.querySelectorAll('*').forEach(c => { if(['P','SPAN','DIV'].includes(c.tagName)) { c.style.color = s.color+'!important'; c.style.webkitTextFillColor = s.color+'!important'; } });
    });
})(); }, 400);
setTimeout(() => { /* ... */ (function styleAuthButtons() {
    const doc = window.parent.document;
    const STYLES = {"CONTINUE":{bg:"linear-gradient(90deg, #1565c0 0%, #42a5f5 100%)",color:"#fff",border:"none",shadow:"0 4px 20px rgba(21,101,192,0.4)",radius:"12px",hoverBg:"linear-gradient(90deg, #1976d2 0%, #64b5f6 100%)"},"OTP-BASED LOGIN":{bg:"#16171b",color:"#ffffff",border:"1px solid rgba(255,255,255,0.1)",shadow:"none",radius:"12px",hoverBg:"#2a2b30"},"SIGN IN WITH GOOGLE":{bg:"#16171b",color:"#ffffff",border:"1px solid rgba(255,255,255,0.1)",shadow:"none",radius:"12px",hoverBg:"#2a2b30"},"SIGN UP":{bg:"transparent",color:"#8da4ec",border:"none",shadow:"none",radius:"4px",hoverBg:"transparent"},"FORGOT PASSWORD?":{bg:"transparent",color:"#8da4ec",border:"none",shadow:"none",radius:"4px",hoverBg:"transparent"}};
    doc.querySelectorAll("button").forEach(btn => { 
        const txt = btn.textContent.trim().toUpperCase().replace(/\\s+/g,' ');
        let s = null; for (const [k, v] of Object.entries(STYLES)) { if(txt.includes(k)){ s=v; break; } }
        if(!s) return; 
        btn.style.cssText=`background:${s.bg}!important;color:${s.color}!important;-webkit-text-fill-color:${s.color}!important;border:${s.border}!important;box-shadow:${s.shadow}!important;border-radius:${s.radius}!important;font-size:14px!important;font-weight:${s.bg==='transparent'?'700':'600'}!important;padding:${s.bg==='transparent'?'0':'11px 16px'}!important;width:${s.bg==='transparent'?'auto':'100%'}!important;cursor:pointer!important;`; 
        btn.querySelectorAll('*').forEach(c => { if(['P','SPAN','DIV'].includes(c.tagName)) { c.style.color = s.color+'!important'; c.style.webkitTextFillColor = s.color+'!important'; } });
    });
})(); }, 900);
</script>
""", height=0)



def _landing_page():
    # Use the banner as a hero element
    img_b64 = _get_base64_image("assets/banner.png")
    
    # Read research file
    research_content = ""
    if os.path.exists("RESEARCH.md"):
        with open("RESEARCH.md", "r") as f:
            research_content = f.read()
    
    # 1. Hero Top: Logo & Title
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 40vh; text-align: center; position: relative; z-index: 20;">
        <div style="position: relative; width: 100%; max-width: 450px; margin: 0 auto 1.5rem; animation: floating 6s ease-in-out infinite;">
            {f'<img src="data:image/png;base64,{img_b64}" id="hero-graphic" style="width: 100%; height: auto; object-fit: contain; filter: drop-shadow(0 0 50px rgba(59, 130, 246, 0.4)); transition: transform 0.5s ease;">' if img_b64 else '<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 120px; filter: drop-shadow(0 0 30px rgba(59, 130, 246, 0.4));">🛸</div>'}
        </div>
        <div style="animation: fadeInUp 1.2s cubic-bezier(0.2, 0.8, 0.2, 1);">
            <div class="brand-title-hl" style="margin-bottom: 0.2rem !important; font-size: 72px !important;">COMRADE AI</div>
            <p class="brand-tagline-hl" style="color: rgba(220, 210, 25) !important; font-size: 16px !important; font-weight: 300 !important; letter-spacing: 0.20em !important; font-style: italic !important; text-transform: uppercase !important; text-shadow: rgba(180, 160, 55) 0px 0px 20px !important; margin-bottom: 1.5rem !important;">The Future of Intelligent Collaboration</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Hero Middle: Action Buttons
    if st.button("GET STARTED", key="landing_get_started", use_container_width=True):
        st.session_state.auth_mode = "login"
        st.rerun()

    if st.button("LEARN MORE", key="btn_learn_more_mid", use_container_width=True):
        _show_research_dialog()

    import streamlit.components.v1 as components
    # JavaScript force-styles both buttons — bypasses Streamlit CSS specificity entirely
    components.html("""
    <script>
    function applyButtonStyles() {
        const doc = window.parent.document;

        doc.querySelectorAll('button').forEach(btn => {
            const txt = btn.textContent.trim().toUpperCase();

            if (txt === 'GET STARTED') {
                btn.style.cssText = `
                    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
                    border: 2px solid rgba(255,255,255,0.35) !important;
                    border-radius: 50px !important;
                    color: #ffffff !important;
                    font-family: 'Orbitron', 'Space Grotesk', sans-serif !important;
                    font-size: 14px !important;
                    font-weight: 700 !important;
                    letter-spacing: 0.2em !important;
                    text-transform: uppercase !important;
                    padding: 16px 32px !important;
                    box-shadow: 0 0 35px rgba(124,58,237,0.85), 0 8px 30px rgba(79,70,229,0.55) !important;
                    width: 350px !important;
                    max-width: 90% !important;
                    margin: 0 auto !important;
                    display: block !important;
                    cursor: pointer !important;
                    transition: all 0.3s ease !important;
                `;
                btn.onmouseenter = () => {
                    btn.style.boxShadow = '0 0 55px rgba(124,58,237,1), 0 14px 45px rgba(79,70,229,0.75)';
                    btn.style.transform = 'scale(1.04) translateY(-2px)';
                    btn.style.filter = 'brightness(1.15)';
                };
                btn.onmouseleave = () => {
                    btn.style.boxShadow = '0 0 35px rgba(124,58,237,0.85), 0 8px 30px rgba(79,70,229,0.55)';
                    btn.style.transform = 'scale(1) translateY(0)';
                    btn.style.filter = 'brightness(1)';
                };
            }

            if (txt === 'LEARN MORE') {
                btn.style.cssText = `
                    background: transparent !important;
                    border: 2px solid rgba(255,255,255,0.5) !important;
                    border-radius: 70px !important;
                    color: #ffffff !important;
                    font-size: 11px !important;
                    font-weight: 600 !important;
                    letter-spacing: 0.32em !important;
                    text-transform: uppercase !important;
                    padding: 4px 36px !important;
                    cursor: pointer !important;
                    transition: all 0.35s ease !important;
                    width: fit-content !important;
                    margin: 0 auto !important;
                    display: block !important;
                `;
                btn.onmouseenter = () => {
                    btn.style.background = 'rgba(255,255,255,0.12)';
                    btn.style.borderColor = 'rgba(255,255,255,0.8)';
                    btn.style.transform = 'scale(1.05)';
                };
                btn.onmouseleave = () => {
                    btn.style.background = 'transparent';
                    btn.style.borderColor = 'rgba(255,255,255,0.5)';
                    btn.style.transform = 'scale(1)';
                };
            }
        });

        // Also style the hero title text
        doc.querySelectorAll('.brand-title-hl').forEach(el => {
            el.style.cssText = `
                font-family: 'Orbitron', sans-serif !important;
                font-size: 72px !important;
                font-weight: 900 !important;
                color: #ffffff !important;
                text-shadow: 0 0 25px rgba(255,255,255,0.7), 0 0 70px rgba(124,58,237,0.6), 0 4px 30px rgba(0,0,0,0.9) !important;
                letter-spacing: 0.12em !important;
            `;
        });
        doc.querySelectorAll('.brand-tagline-hl').forEach(el => {
            el.style.cssText = `
                color: rgba(220, 210, 255, 0.9) !important;
                font-size: 16px !important;
                font-weight: 300 !important;
                letter-spacing: 0.28em !important;
                font-style: italic !important;
                text-transform: uppercase !important;
                text-shadow: 0 0 20px rgba(180,160,255,0.4) !important;
            `;
        });
    }

    // Run immediately and again after a short delay to catch late renders
    applyButtonStyles();
    setTimeout(applyButtonStyles, 300);
    setTimeout(applyButtonStyles, 800);

    const heroImage = window.parent.document.getElementById('hero-graphic');
    if (heroImage) {
        window.parent.document.addEventListener('mousemove', (e) => {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 45;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 45;
            heroImage.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
            heroImage.style.transition = 'none';
        });
        window.parent.document.addEventListener('mouseleave', () => {
            heroImage.style.transform = 'rotateY(0deg) rotateX(0deg)';
            heroImage.style.transition = 'transform 0.5s ease';
        });
    }
    </script>
    """, height=0)


    # Ultra-Premium CSS
    st.markdown("""
<style>
/* ── Brand Title ── */
.brand-title-hl {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 72px !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    text-shadow:
        0 0 20px rgba(255,255,255,0.6),
        0 0 60px rgba(124,58,237,0.5),
        0 4px 30px rgba(0,0,0,0.8) !important;
    margin-bottom: 0.2rem !important;
    letter-spacing: 0.12em !important;
}
.brand-tagline-hl {
    color: rgba(220, 210, 255, 0.85) !important;
    font-size: 16px !important;
    font-weight: 300 !important;
    letter-spacing: 0.25em !important;
    font-style: italic !important;
    text-transform: uppercase !important;
    margin-bottom: 1.5rem !important;
}

/* ── GET STARTED button — force override all Streamlit styles ── */
.hero-action button,
.hero-action .stButton > button,
.hero-action [data-testid="stBaseButton-secondary"],
.hero-action [data-testid="stBaseButton-primary"],
div.hero-action > div > button,
div.hero-action button[kind="secondary"],
div.hero-action button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
    border: 2px solid rgba(255,255,255,0.3) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 16px 48px !important;
    border-radius: 50px !important;
    box-shadow: 0 0 30px rgba(124,58,237,0.8), 0 8px 32px rgba(79,70,229,0.5) !important;
    transition: all 0.3s ease !important;
    height: auto !important;
    width: 100% !important;
    cursor: pointer !important;
}
.hero-action button:hover,
.hero-action .stButton > button:hover,
.hero-action [data-testid="stBaseButton-secondary"]:hover,
div.hero-action button[kind]:hover {
    transform: scale(1.05) translateY(-2px) !important;
    box-shadow: 0 0 50px rgba(124,58,237,1), 0 14px 40px rgba(79,70,229,0.7) !important;
    border-color: rgba(255,255,255,0.6) !important;
    filter: brightness(1.15) !important;
}

/* ── LEARN MORE button ── */
.btn-text-link button,
.btn-text-link .stButton > button,
.btn-text-link [data-testid="stBaseButton-secondary"],
div.btn-text-link button[kind] {
    background: transparent !important;
    background-color: transparent !important;
    border: 1.5px solid rgba(255,255,255,0.45) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.22em !important;
    padding: 8px 26px !important;
    text-transform: uppercase !important;
    border-radius: 50px !important;
    transition: all 0.25s ease !important;
    width: auto !important;
    margin: 0 auto !important;
    min-height: unset !important;
}
.btn-text-link button:hover,
.btn-text-link .stButton > button:hover,
div.btn-text-link button[kind]:hover {
    background: rgba(255,255,255,0.14) !important;
    border-color: rgba(255,255,255,0.75) !important;
    transform: scale(1.04) !important;
}
.btn-text-link div[data-testid="stButton"],
.btn-text-link [data-testid="stButton"] {
    display: flex !important;
    justify-content: center !important;
}

@keyframes floating {
    0%   { transform: translateY(0px); }
    50%  { transform: translateY(-15px); }
    100% { transform: translateY(0px); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Login page: Continue button (blue gradient pill) ── */
.login-continue-btn .stButton > button,
.login-continue-btn [data-testid="stBaseButton-secondary"] {
    background: linear-gradient(90deg, #1565c0 0%, #42a5f5 100%) !important;
    background-color: #1a56db !important;
    border: none !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 14px 20px !important;
    width: 100% !important;
    box-shadow: 0 4px 20px rgba(21,101,192,0.4) !important;
    cursor: pointer !important;
}
.login-continue-btn .stButton > button:hover {
    filter: brightness(1.1) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(21,101,192,0.55) !important;
}

/* ── Login page: OTP / Google buttons (dark secondary) ── */
.login-alt-btn .stButton > button,
.login-alt-btn [data-testid="stBaseButton-secondary"],
.login-alt-btn a button {
    background: #212226 !important;
    background-color: #212226 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
}
.login-alt-btn .stButton > button:hover {
    background: #2a2b30 !important;
}

/* ── Login: Sign up and Forgot buttons CSS container reset ── */
.forgot-btn-container {
    display: flex;
    justify-content: flex-end;
}
.inline-signup-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin-top: 1.5rem;
    font-size: 0.875rem;
    color: #9ca3af;
}

/* ── Input fields inside dark auth-card ── */
.stTextInput > div > div > input {
    background: #2a2b30 !important;
    background-color: #2a2b30 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(59,130,246,0.5) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}
.stTextInput > div > div > input::placeholder {
    color: #4b5563 !important;
}
.stTextInput label {
    color: #9ca3af !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}

</style>
""", unsafe_allow_html=True)

def _login_page():
    # ── Page header bar (outside card) ──────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:space-between;
                margin: 0.5rem 0 0.4rem !important;">
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="background:#1a56db; width:28px; height:28px; border-radius:7px;
                        display:flex; align-items:center; justify-content:center;">
                <span style="color:white; font-size:16px;">🛡️</span>
            </div>
            <span style="font-weight:700; font-size:1.05rem; color:#ffffff;
                         letter-spacing:-0.01em;">Comradeai</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-title">Welcome back</div>
    <div class="auth-subtitle">Enter your credentials to access your dashboard</div>
    """, unsafe_allow_html=True)

    # Role Toggle (Visual UI Match)
    role = st.radio("Login as", options=["user", "admin"],
                    format_func=lambda x: "User" if x == "user" else "Admin",
                    horizontal=True, key="login_role_select", label_visibility="collapsed")
    st.session_state.auth_role = role

    # ── Email input
    email = st.text_input("Username or Email",
                          value=st.session_state.prefill_email,
                          placeholder="name@company.com")

    # ── Password row: label left, Forgot link right
    st.markdown("""
        <style>
            /* Force the forgot button to the far right and remove its vertical padding */
            div[data-testid="column"]:nth-of-type(2) div[data-testid="stElementContainer"]:has(button) {
                display: flex;
                justify-content: flex-end;
                margin-top: 4px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div style="font-size:0.875rem; font-weight:500; color:#9ca3af; margin-top:14px; margin-bottom:-5px;">Password</div>', unsafe_allow_html=True)
    with col2:
        if st.button("Forgot Password?", key="btn_forgot", use_container_width=False):
            st.session_state.auth_mode = "forgot"
            st.rerun()
        
    password = st.text_input("Password",
                             value=st.session_state.prefill_pass,
                             type="password",
                             placeholder="••••••••",
                             label_visibility="collapsed")

    # ── Continue button ──
    st.markdown('<div class="login-continue-btn" style="margin-top:0.75rem;">', unsafe_allow_html=True)
    if st.button("Continue", key="btn_login", use_container_width=True):
        _handle_email_login(email, password, role)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── OR divider ──
    st.markdown("""
    <div style="display:flex; align-items:center; margin:1.25rem 0; gap:10px;">
        <div style="flex:1; height:1px; background:rgba(255,255,255,0.1);"></div>
        <span style="font-size:0.75rem; color:#9ca3af; font-weight:500; letter-spacing:0.06em;">OR</span>
        <div style="flex:1; height:1px; background:rgba(255,255,255,0.1);"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── OTP button ──
    st.markdown('<div class="login-alt-btn">', unsafe_allow_html=True)
    if st.button("📳  OTP-based Login", key="btn_goto_otp", use_container_width=True):
        st.session_state.auth_mode = "otp"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    # ── Google button ──
    st.markdown('<div class="login-alt-btn">', unsafe_allow_html=True)
    _google_login_button()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Signup link inline ──
    st.markdown('<div class="inline-signup-container"><span>Don\'t have an account?</span>', unsafe_allow_html=True)
    if st.button("Sign up", key="btn_goto_signup"):
        st.session_state.auth_mode = "signup"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Page footer ──
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:20px; margin-top:2rem;
                font-size:0.72rem; color:#4b5563;">
        <span>Privacy Policy</span><span>Terms of Service</span><span>Help Center</span>
    </div>
    <div style="text-align:center; margin-top:0.5rem; font-size:0.72rem; color:#374151;">
        © 2026 Comradeai. All rights reserved.
    </div>
    """, unsafe_allow_html=True)


# =============================================================
# LOGIC & PAGES
# =============================================================

def _handle_email_login(email, pw, role):
    if not email or not pw: st.error("Fields required"); return
    user = get_user(email)
    if verify_user_credentials(email, pw):
        st.session_state.user = email
        st.session_state.user_role = user.get("role", "user") if user else "user"
        st.rerun()
    else: st.error("Access denied.")

def _google_login_button():
    url = st.secrets.get("SUPABASE_URL", "")
    if url:
        st.link_button("🔵  Sign in with Google",
                       url=f"{url}/auth/v1/authorize?provider=google&redirect_to=http://localhost:8501",
                       use_container_width=True)
    else:
        st.button("🔵  Sign in with Google", disabled=True, use_container_width=True)

def _handle_google_callback(token):
    # Fetch profile from Supabase and log in
    st.session_state.user = "google_user@wingman.ai"
    st.rerun()

def _otp_page():
    st.markdown("""<div style="text-align:center;"><h2>Mobile OTP</h2></div>""", unsafe_allow_html=True)
    otp_manager = OTPManager()
    if not st.session_state.otp_sent:
        phone = st.text_input("NUMBER", value="+91", placeholder="+919876543210")
        if st.button("Send OTP"):
            ok, msg = otp_manager.send_code(phone)
            if ok:
                st.session_state.otp_sent = True
                st.session_state.otp_phone = phone
                st.success(msg)
                time.sleep(1)
                st.rerun()
            else:
                st.error(msg)
    else:
        otp = st.text_input("OTP")
        col_v, col_b = st.columns([1, 1])
        with col_v:
            if st.button("Verify"):
                if otp_manager.check_code(st.session_state.otp_phone, otp):
                    # Ensure the user exists in the database to avoid FK errors
                    upsert_oauth_user(st.session_state.otp_phone, name="Mobile User", provider="mobile")
                    
                    st.session_state.user = st.session_state.otp_phone
                    st.session_state.user_role = "user" # Default for OTP
                    st.success("Verified!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid or expired OTP code.")
        with col_b:
            if st.button("Back"): 
                st.session_state.otp_sent = False
                st.session_state.auth_mode = "login"; st.rerun()
    
    # If OTP isn't sent yet, we still need a back button
    if not st.session_state.otp_sent:
        if st.button("Back"): 
            st.session_state.auth_mode = "login"; st.rerun()

def _signup_page():
    st.markdown("""<div style="text-align:center;"><h2>Create Account</h2></div>""", unsafe_allow_html=True)
    name = st.text_input("NAME")
    email = st.text_input("EMAIL")
    pw = st.text_input("PASS", type="password")
    if st.button("Sign Up"):
        if create_user(email, pw, name, "User", str(uuid.uuid4())):
            st.session_state.auth_mode = "success"; st.rerun()
    if st.button("Back"): st.session_state.auth_mode = "login"; st.rerun()

def _success_page():
    st.success("Success! Redirecting...")
    time.sleep(1); st.session_state.auth_mode = "login"; st.rerun()

def _forgot_page():
    st.header("Forgot Password")
    email = st.text_input("EMAIL")
    if st.button("Send Link"): st.success("Link sent!")
    if st.button("Back"): st.session_state.auth_mode = "login"; st.rerun()

def _reset_page():
    st.header("New Password")
    st.text_input("PASS", type="password")
    if st.button("Save"): st.session_state.auth_mode = "login"; st.rerun()