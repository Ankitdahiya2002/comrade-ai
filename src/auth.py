# =============================================================
# src/auth.py
# Authentication — three ways to sign in, pure Streamlit Python.
#
# METHOD 1 — Email + Password (manual)
#   - Signup collects name, profession, email, password, captcha
#   - Live password-strength meter
#   - Inline field errors (not generic toasts)
#   - Email verification link sent on signup
#   - 3-second countdown redirect after successful signup
#   - Forgot / reset password via email link
#
# METHOD 2 — Google OAuth (one click)
#   - Redirects to Supabase Auth → Google → back to app
#   - On return, reads the user from the ?access_token URL param
#   - Creates the user row in DB automatically if first visit
#   - Works with or without Supabase (shows info message otherwise)
#
# METHOD 3 — Mobile OTP
#   - User enters phone number → 6-digit OTP sent via Twilio Verify
#   - User enters OTP → verified and logged in
#   - Dev mode: shows OTP on screen (no Twilio keys needed)
#   - Creates the user row in DB automatically on first login
#
# ROLE ROUTING
#   - USER / ADMIN radio on the login page
#   - Admin must use email+password (no OAuth for admins)
#   - Blocked users cannot log in regardless of method
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


# ── Session defaults — set once on first load ─────────────────
for key, default in [
    ("auth_mode",    "login"),
    ("auth_role",    "user"),
    ("prefill_email", ""),
    ("otp_phone",    ""),
    ("otp_sent",     False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# =============================================================
# CSS — applied to every auth page
# =============================================================

def _apply_auth_css():
    """Premium dark glassmorphism login UI with animated gradient and neon accents."""
    # Inject Google Fonts separately to avoid Streamlit's parser stripping <link> tags
    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">',
        unsafe_allow_html=True
    )
    st.markdown("""
<style>

/* ── Base + ALL Streamlit containers forced dark ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMainBlockContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
.main, .block-container {
    background: #0a0a0f !important;
    color: #e8e6f0 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    overflow: hidden !important;
}
[data-testid="stMainBlockContainer"] {
    padding-top: 2rem !important;
    padding-bottom: 0 !important;
}
[data-testid="column"] {
    background: transparent !important;
}
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background: 
        radial-gradient(ellipse 80% 60% at 20% -20%, rgba(25,195,125,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 100%, rgba(83,70,218,0.12) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 50% 50%, rgba(0,0,0,0) 0%, rgba(10,10,15,0.8) 100%);
    pointer-events: none;
    z-index: 0;
    animation: bgPulse 8s ease-in-out infinite alternate;
}
@keyframes bgPulse {
    from { opacity: 0.7; }
    to   { opacity: 1.0; }
}
[data-testid="stSidebar"]  { display: none !important; }
#MainMenu, footer, header,
[data-testid="stToolbar"],
.stDeployButton            { display: none !important; }
[data-testid="stMainBlockContainer"] { position: relative; z-index: 1; }

/* ── All buttons ── */
.stButton > button {
    width: 100% !important;
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e8e6f0 !important;
    border-radius: 12px !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    padding: 11px 18px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.09) !important;
    border-color: rgba(25,195,125,0.4) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(25,195,125,0.12) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Neon green primary button ── */
.primary-btn .stButton > button {
    background: linear-gradient(135deg, #19c37d 0%, #0fa86a 100%) !important;
    border-color: transparent !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 24px rgba(25,195,125,0.35), 0 0 0 0 rgba(25,195,125,0.4) !important;
}
.primary-btn .stButton > button:hover {
    box-shadow: 0 6px 32px rgba(25,195,125,0.5), 0 0 0 4px rgba(25,195,125,0.12) !important;
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #1fd88c 0%, #14b874 100%) !important;
    border-color: transparent !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #e8e6f0 !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 13px 18px !important;
    transition: all 0.2s ease !important;
    backdrop-filter: blur(10px) !important;
}
.stTextInput > div > div > input::placeholder {
    color: rgba(200,200,220,0.35) !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(25,195,125,0.6) !important;
    box-shadow: 0 0 0 3px rgba(25,195,125,0.12), 0 0 20px rgba(25,195,125,0.08) !important;
    background: rgba(25,195,125,0.04) !important;
}
.stTextInput label {
    color: rgba(200,200,220,0.7) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

/* ── Radio (role selector) ── */
.stRadio > div { flex-direction: row !important; gap: 8px !important; }
.stRadio label {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    padding: 8px 20px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    color: rgba(200,200,220,0.7) !important;
    transition: all 0.2s ease !important;
}
.stRadio label:has(input:checked) {
    background: rgba(25,195,125,0.15) !important;
    border-color: rgba(25,195,125,0.5) !important;
    color: #19c37d !important;
}

/* ── Misc ── */
.stCheckbox label { font-size: 13px !important; color: rgba(200,200,220,0.6) !important; }
.stProgress > div > div { background: linear-gradient(90deg, #19c37d, #5436da) !important; border-radius: 4px !important; }
hr { border-color: rgba(255,255,255,0.07) !important; }

/* ── Social login divider ── */
.social-divider {{
    display: flex;
    align-items: center;
    text-align: center;
    margin: 20px 0;
    color: rgba(200,200,220,0.3) !important;
}}
.social-divider::before, .social-divider::after {{
    content: '';
    flex: 1;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}}
.social-divider:not(:empty)::before {{ margin-right: .5em; }}
.social-divider:not(:empty)::after {{ margin-left: .5em; }}

/* ── Social buttons ── */
.social-btn .stButton > button {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    height: 52px !important;
    width: 100% !important;
    border-radius: 14px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
.social-btn .stButton > button:hover {{
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(25,195,125,0.4) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}}
.social-google .stButton > button {{
    background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0OCA0OCIgd2lkdGg9IjI0cHgiIGhlaWdodD0iMjRweCI+PHBhdGggZmlsbD0iI0ZGQzEwNyIgZD0iTTQzLjYxMSwyMC4wODNINDJWMjBIMjR2OGgxMS4zMDNjLTEuNjQ5LDQuNjU3LTYuMDgsOC0xMS4zMDMsOGMtNi42MjcsMC0xMi01LjM3My0xMi0xMmMwLTYuNjI3LDUuMzczLTEyLDEyLTEyYzMuMDU5LDAsNS44NDIsMS4xNTQsNy45NjEsMy4wMzlsczUuNjU3LTUuNjU3QzM0LjA0Niw2LjA1MywyOS4yNjgsNCwyNCw0QzEyLjk1NSw0LDQsMTIuOTU1LDQsMjRzOC45NTUsMjAsMjAsMjBzMjAtOC45NTUsMjAtMjBDNDQsMjIuNjU5LDQzLjg2MiwyMS4zNTAsNDMuNjExLDIwLjA4M3oiLz48cGF0aCBmaWxsPSIjRkYzRDAwIiBkPSJNNi4zMDYsMTQuNjkxbDYuNTcxLDQuODE5QzE0LjY1NSwxNS4xMDgsMTguOTYxLDEyLDI0LDEyYzMuMDU5LDAsNS44NDIsMS4xNTQsNy45NjEsMy4wMzlsczUuNjU3LTUuNjU3QzM0LjA0Niw2LjA1MywyOS4yNjgsNCwyNCw0QzE2LjMxOCw0LDkuNjU2LDguMzM3LDYuMzA2LDE0LjY5MXoiLz48cGF0aCBmaWxsPSIjNENBRjUwIiBkPSJNMjQsNDRjNS4xNjYsMCw5Ljg2LTEuOTc3LDEzLjQwOS01LjE5MmwtNi4xOS01LjIzOEMyOS4yMTEsMzUuMDkxLDI2LjcxNSwzNiwyNCwzNmMtNS4yMDIsMC05LjYxOS0zLjMxNy0xMS4yODMtNy45NDZsLTYuNTIyLDUuMDI1QzkuNTA1LDM5LjU1NiwxNi4yMjcsNDQsMjQsNDR6Ii8+PHBhdGggZmlsbD0iIzE5NzZEMiIgZD0iTTQzLjYxMSwyMC4wODNINDJWMjBIMjR2OGgxMS4zMDNjLTAuNzkyLDIuMjM3LTIuMjMxLDQuMTY2LTQuMDg3LDUuNTcxYzAuMDAxLTAuMDAxLDAuMDAyLTAuMDAxLDAuMDAzLTAuMDAybDYuMTksNS4yMzhDMzYuOTcxLDM5LjIwNSw0NCwzNCw0NCwyNEM0NCwyMi42NTksNDMuODYyLDIxLjM1MCw0My42MTEsMjAuMDgzeiIvPjwvc3ZnPg==') !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 24px !important;
}}
.social-phone .stButton > button {{
    background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMxOWMzN2QiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjIgMTYuOTJ2M2EyIDIgMCAwIDEtMi4xOCAyIDE5Ljc5IDE5Ljc5IDAgMCAxLTguNjMtMy4wNyAxOS41IDE5LjUgMCAwIDEtNi02IDE5Ljc5IDE5Ljc5IDAgMCAxLTMuMDctOC42N0EyIDIgMCAwIDEgNC4xMSAySDcuMTFhMiAyIDAgMCAxIDIgMS43MiAxMi44NCAxMi44NCAwIDAgMCAuNyAyLjgxIDIgMiAwIDAgMS0uNDUgMi4xMUw4LjA5IDkuOTFhMTYgMTYgMCAwIDAgNiA2bDEuMjctMS4yN2EyIDIgMCAwIDEgMi4xMS0uNDUgMTIuODQgMTIuODQgMCAwIDAgMi44MS43QTIgMiAwIDAgMSAyMiAxNi45MnoiPjwvcGF0aD48L3N2Zz4=') !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 22px !important;
}}

</style>
""", unsafe_allow_html=True)


# =============================================================
# PUBLIC ENTRY POINT
# =============================================================

def auth_page():
    """
    Main entry point — called by app.py when no user is logged in.
    Reads URL params to handle email-verify and password-reset links.
    Routes to the correct page based on st.session_state.auth_mode.
    """
    _apply_auth_css()

    # ── Handle ?verify_token=... in the URL ───────────────────
    verify_token = st.query_params.get("verify_token")
    if verify_token:
        t = verify_token[0] if isinstance(verify_token, list) else verify_token
        if verify_user_token(t):
            st.success("✅ Email verified. You can now log in.")
        else:
            st.error("❌ This verification link is invalid or has expired.")

    # ── Handle ?reset_token=... in the URL ────────────────────
    reset_token = st.query_params.get("reset_token")
    if reset_token:
        st.session_state.auth_mode   = "reset"
        st.session_state.reset_token = (
            reset_token[0] if isinstance(reset_token, list) else reset_token
        )

    # ── Handle Google OAuth callback (#fragment to ?query) ──
    # Streamlit cannot natively read fragments, so we convert it via JS and reload.
    import streamlit.components.v1 as components
    components.html("""
<script>
    const hash = window.parent.location.hash;
    if (hash && (hash.includes('access_token=') || hash.includes('id_token='))) {
        // Convert '#' to '?' and reload the parent window
        const newUrl = window.parent.location.href.split('#')[0] + '?' + hash.substring(1);
        window.parent.location.href = newUrl;
    }
</script>
""", height=0)

    # ── Handle Google OAuth callback (?access_token=...) ──────
    access_token = st.query_params.get("access_token")
    if access_token:
        _handle_google_callback(
            access_token[0] if isinstance(access_token, list) else access_token
        )
        return  # Logged in — app.py will rerun and show the chat UI

    # ── Route to the correct page ─────────────────────────────
    pages = {
        "login":   _login_page,
        "signup":  _signup_page,
        "otp":     _otp_page,
        "forgot":  _forgot_page,
        "reset":   _reset_page,
        "success": _success_page,
    }
    pages.get(st.session_state.auth_mode, _login_page)()


# =============================================================
# LOGIN PAGE
# =============================================================

def _login_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # ── Logo + title ──────────────────────────────────────
        st.markdown("""
<div style="text-align:center; margin-bottom:28px;">
  <div style="font-size:44px; margin-bottom:8px;">🤖</div>
  <h1 style="font-size:26px; font-weight:600; color:#ececec;
             letter-spacing:-0.5px; margin:0;">
    Welcome back
  </h1>
  <p style="font-size:14px; color:#8e8ea0; margin-top:6px;">
    Sign in to Wingman AI
  </p>
</div>
""", unsafe_allow_html=True)

        # ── Role selector ─────────────────────────────────────
        role = st.radio(
            "Role",
            options=["user", "admin"],
            format_func=lambda x: "👤  User" if x == "user" else "👑  Admin",
            horizontal=True,
            index=0 if st.session_state.auth_role == "user" else 1,
            label_visibility="collapsed",
        )
        st.session_state.auth_role = role
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Email + password fields ───────────────────────────
        email    = st.text_input("Email",    value=st.session_state.prefill_email,
                                 placeholder="you@example.com")
        password = st.text_input("Password", type="password",
                                 placeholder="Enter your password")

        col_rem, col_fgt = st.columns(2)
        with col_rem:
            st.checkbox("Remember me")
        with col_fgt:
            if st.button("Forgot password?", key="btn_forgot"):
                st.session_state.auth_mode = "forgot"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Primary login button
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("Continue", key="btn_login"):
            _handle_email_login(email, password, role)
        st.markdown('</div>', unsafe_allow_html=True)

        # Social options — only for users, not admins
        if role == "user":
            st.markdown('<div class="social-divider">Or continue with</div>', unsafe_allow_html=True)
            
            social_col1, social_col2 = st.columns(2)
            with social_col1:
                st.markdown('<div class="social-btn social-google" title="Continue with Google">', unsafe_allow_html=True)
                _google_login_button()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with social_col2:
                st.markdown('<div class="social-btn social-phone" title="Continue with Mobile">', unsafe_allow_html=True)
                if st.button("", key="btn_goto_otp"):
                    st.session_state.auth_mode = "otp"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Create account →", key="btn_goto_signup"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()
            with col_b:
                st.markdown(
                    '<p style="font-size:12px;color:#8e8ea0;'
                    'text-align:right;padding-top:8px;">Free forever</p>',
                    unsafe_allow_html=True,
                )


def _handle_email_login(email: str, password: str, role: str):
    """Validate email + password and set session state on success."""
    if not email or not password:
        st.warning("Please enter your email and password.")
        return

    user = get_user(email)

    # Prevent admins from logging in as users and vice versa
    if user and user.get("role") == "admin" and role != "admin":
        st.error("❌ This is an admin account. Select 'Admin' above.")
        return
    if user and user.get("role") != "admin" and role == "admin":
        st.error("❌ This account does not have admin access.")
        return

    if verify_user_credentials(email, password):
        st.session_state.user          = email
        st.session_state.user_role     = user.get("role", "user")
        st.session_state.prefill_email = ""
        st.rerun()
    else:
        if user and user.get("blocked"):
            st.error("🔒 This account has been blocked. Contact support.")
        else:
            st.error("❌ Incorrect email or password.")


# =============================================================
# GOOGLE OAUTH  (Method 2)
# =============================================================

def _google_login_button():
    """
    Show a 'Continue with Google' button.
    Clicking it redirects to Supabase → Google → back to the app.
    On return, the URL will contain ?access_token=... which
    _handle_google_callback() processes.
    """
    supabase_url = st.secrets.get("SUPABASE_URL", "")
    base_url     = st.secrets.get("BASE_URL", "http://localhost:8501")

    if not supabase_url:
        st.info("💡 Add SUPABASE_URL to secrets.toml to enable Google login.")
        return

    # Build the Supabase OAuth redirect URL
    redirect_url = f"{base_url}"
    oauth_url    = (
        f"{supabase_url}/auth/v1/authorize"
        f"?provider=google"
        f"&redirect_to={redirect_url}"
    )

    # Use st.link_button with a Google 'G' emoji or label
    # Empty label because the icon is injected as a background-image via CSS
    st.link_button("", url=oauth_url, use_container_width=True)


def _handle_google_callback(access_token: str):
    """
    Called when Google redirects back with ?access_token=...
    Fetches the user's profile from Supabase Auth using the token,
    creates/fetches the user row in our users table, and logs them in.
    """
    supabase_url = st.secrets.get("SUPABASE_URL", "")
    supabase_key = st.secrets.get("SUPABASE_KEY", "")

    if not supabase_url or not supabase_key:
        st.error("❌ Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY to secrets.")
        return

    try:
        # Ask Supabase Auth for the user's profile
        resp = requests.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey":        supabase_key,
                "Authorization": f"Bearer {access_token}",
            },
            timeout=10,
        )

        if resp.status_code != 200:
            st.error("❌ Google login failed. Please try again.")
            return

        profile   = resp.json()
        email     = profile.get("email", "")
        full_name = profile.get("user_metadata", {}).get("full_name", email.split("@")[0])

        if not email:
            st.error("❌ Could not retrieve email from Google account.")
            return

        # Create the user row if this is their first login
        user = upsert_oauth_user(email, full_name, provider="google")

        if user.get("blocked"):
            st.error("🔒 This account has been blocked. Contact support.")
            return

        # Log them in
        st.session_state.user      = email
        st.session_state.user_role = user.get("role", "user")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Google login error: {e}")


# =============================================================
# MOBILE OTP  (Method 3)
# =============================================================

def _otp_page():
    """
    Two-step OTP login:
    Step A — user enters phone number → OTP is sent
    Step B — user enters OTP → verified and logged in
    """
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
<div style="text-align:center; margin-bottom:24px;">
  <div style="font-size:40px; margin-bottom:8px;">📱</div>
  <h1 style="font-size:24px; font-weight:600; color:#ececec; margin:0;">
    Sign in with OTP
  </h1>
  <p style="font-size:13px; color:#8e8ea0; margin-top:6px;">
    We'll send a 6-digit code to your mobile
  </p>
</div>
""", unsafe_allow_html=True)

        if not st.session_state.otp_sent:
            # ── Step A: enter phone number ────────────────────
            phone = st.text_input(
                "Mobile number",
                placeholder="+919876543210",
                help="Include country code, e.g. +91 for India",
            )
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("Send OTP", key="btn_send_otp"):
                if not re.match(r"^\+?[0-9\s]{10,20}$", phone.strip()):
                    st.error("❌ Enter a valid mobile number with country code.")
                else:
                    # Remove all whitespace to prevent Twilio mismatches
                    clean_phone = phone.replace(" ", "")
                    ok, msg = _send_otp(clean_phone)
                    if ok:
                        st.session_state.otp_phone = clean_phone
                        st.session_state.otp_sent  = True
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            # ── Step B: enter OTP ─────────────────────────────
            st.info(f"OTP sent to **{st.session_state.otp_phone}**")
            otp = st.text_input(
                "Enter the 6-digit code",
                max_chars=6,
                placeholder="123456",
            )
            st.markdown("<br>", unsafe_allow_html=True)

            col_verify, col_resend = st.columns(2)

            with col_verify:
                st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                if st.button("Verify & Sign in", key="btn_verify_otp"):
                    _verify_otp_and_login(otp)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_resend:
                if st.button("Resend OTP", key="btn_resend_otp"):
                    ok, msg = _send_otp(st.session_state.otp_phone)
                    if ok:
                        st.success("✅ New OTP sent!")
                    else:
                        st.error(f"❌ {msg}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to login", key="btn_back_otp"):
            st.session_state.otp_sent  = False
            st.session_state.otp_phone = ""
            st.session_state.auth_mode = "login"
            st.rerun()


def _send_otp(phone: str) -> tuple[bool, str]:
    """
    Send a 6-digit OTP via Twilio Verify.
    Returns (True, "sent") on success, or (False, error_message).

    Dev mode: if Twilio keys are not set, a random OTP is generated
    and displayed on screen — useful for local testing.
    """
    account_sid = st.secrets.get("TWILIO_ACCOUNT_SID", "")
    auth_token  = st.secrets.get("TWILIO_AUTH_TOKEN",  "")
    verify_sid  = st.secrets.get("TWILIO_VERIFY_SID",  "")

    # ── Real SMS via Twilio ───────────────────────────────────
    if account_sid and auth_token and verify_sid:
        try:
            resp = requests.post(
                f"https://verify.twilio.com/v2/Services/{verify_sid}/Verifications",
                auth=(account_sid, auth_token),
                data={"To": phone, "Channel": "sms"},
                timeout=15,
            )
            if resp.status_code in (200, 201):
                return True, "sent"
            return False, f"Twilio error {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, str(e)

    # ── Dev mode — show OTP on screen ────────────────────────
    dev_otp = str(random.randint(100000, 999999))
    # Store in session so _verify_otp_and_login can check it
    st.session_state["_dev_otp"] = dev_otp
    st.info(
        f"🔧 **Dev mode** — Twilio keys not set.  \n"
        f"Your OTP is: **{dev_otp}**  \n"
        f"Add TWILIO_* keys to secrets.toml for real SMS."
    )
    return True, "dev"


def _verify_otp_and_login(entered_otp: str):
    """
    Verify the OTP. Uses Twilio Verify for real OTPs,
    or compares against the dev OTP stored in session state.
    On success, creates/fetches the user and logs them in.
    """
    phone = st.session_state.otp_phone

    account_sid = st.secrets.get("TWILIO_ACCOUNT_SID", "")
    auth_token  = st.secrets.get("TWILIO_AUTH_TOKEN",  "")
    verify_sid  = st.secrets.get("TWILIO_VERIFY_SID",  "")

    verified = False

    # ── Real verification via Twilio ──────────────────────────
    if account_sid and auth_token and verify_sid:
        try:
            resp = requests.post(
                f"https://verify.twilio.com/v2/Services/{verify_sid}/VerificationCheck",
                auth=(account_sid, auth_token),
                data={"To": phone, "Code": entered_otp},
                timeout=15,
            )
            data = resp.json()
            verified = data.get("status") == "approved"
        except Exception as e:
            st.error(f"❌ Twilio verification failed: {e}")
            return

    # ── Dev mode check ────────────────────────────────────────
    else:
        verified = (entered_otp == st.session_state.get("_dev_otp", ""))

    if not verified:
        st.error("❌ Incorrect OTP. Please check the code and try again.")
        return

    # ── OTP correct — log the user in ────────────────────────
    # Use a synthetic email for phone-only users
    phone_email = f"{phone.lstrip('+').replace(' ', '')}@otp.wingman.ai"
    display_name = phone  # Shown in the sidebar until they update their profile

    user = upsert_oauth_user(phone_email, display_name, provider="phone")

    if user.get("blocked"):
        st.error("🔒 This account has been blocked. Contact support.")
        return

    st.session_state.user      = phone_email
    st.session_state.user_role = user.get("role", "user")
    st.session_state.otp_sent  = False
    st.session_state.otp_phone = ""
    st.session_state.pop("_dev_otp", None)
    st.rerun()


# =============================================================
# SIGNUP PAGE  (email + password — manual registration)
# =============================================================

def _signup_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
<div style="text-align:center; margin-bottom:24px;">
  <div style="font-size:38px; margin-bottom:8px;">🤖</div>
  <h1 style="font-size:24px; font-weight:600; color:#ececec; margin:0;">
    Create your account
  </h1>
  <p style="font-size:13px; color:#8e8ea0; margin-top:6px;">
    Free forever · No credit card required
  </p>
</div>
""", unsafe_allow_html=True)

        name       = st.text_input("Full name",         placeholder="Ankit Kumar")
        profession = st.text_input("Profession / role", placeholder="Software Engineer")
        email      = st.text_input("Email address",     placeholder="you@example.com")
        password   = st.text_input("Password",          placeholder="Minimum 8 characters",
                                   type="password")
        confirm    = st.text_input("Confirm password",  placeholder="Repeat your password",
                                   type="password")

        # Live password strength bar
        if password:
            score = sum([
                len(password) >= 8,
                bool(re.search(r"[A-Z]", password)),
                bool(re.search(r"[0-9]", password)),
                bool(re.search(r"[^a-zA-Z0-9]", password)),
            ])
            st.progress(score / 4)
            st.caption(
                f"Password strength: "
                f"{['', 'Weak', 'Fair', 'Good', 'Strong ✓'][score]}"
            )

        captcha = st.checkbox("✅  I am not a robot")
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("Create account", key="btn_signup"):
            _handle_signup(name, profession, email, password, confirm, captcha)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to login", key="btn_back_signup"):
            st.session_state.auth_mode = "login"
            st.rerun()


def _handle_signup(name, profession, email, password, confirm, captcha):
    """Validate the signup form and create the account if all fields are valid."""
    errors = []

    if not name.strip():
        errors.append("Full name is required.")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append("Please enter a valid email address.")
    elif get_user(email):
        errors.append("This email is already registered. Try logging in.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    elif password != confirm:
        errors.append("Passwords do not match.")
    if not captcha:
        errors.append("Please check the 'I am not a robot' box.")

    # Show every error at once so the user can fix them all in one go
    for error in errors:
        st.error(f"❌ {error}")

    if errors:
        return  # Do not create the account

    # Animate progress while the account is being created
    bar = st.progress(0, text="Creating your account…")
    for pct in [25, 55, 85]:
        time.sleep(0.2)
        bar.progress(pct)

    # Store raw password for testing/college project purposes
    hashed = password
    token  = str(uuid.uuid4())
    ok     = create_user(email, hashed, name, profession, token)
    bar.progress(100)

    if ok:
        send_verification_email(email, token)
        st.session_state.prefill_email = email
        st.session_state.auth_mode     = "success"
        st.rerun()
    else:
        st.error("❌ Could not create the account. Please try again.")


# =============================================================
# SUCCESS PAGE — shown after signup, auto-redirects to login
# =============================================================

def _success_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        email = st.session_state.get("prefill_email", "your email")

        st.markdown(f"""
<div style="text-align:center; padding:20px 0;">
  <div style="font-size:52px; margin-bottom:14px;">✅</div>
  <h2 style="color:#ececec; font-size:22px; margin-bottom:8px;">
    Account created!
  </h2>
  <p style="color:#8e8ea0; font-size:14px; line-height:1.6;">
    We sent a verification link to<br>
    <strong style="color:#ececec;">{email}</strong><br>
    Click the link in your inbox to activate your account.
  </p>
</div>
""", unsafe_allow_html=True)

        # 3-second countdown redirect
        for seconds_left in range(3, 0, -1):
            st.info(f"Redirecting to login in {seconds_left}…")
            time.sleep(1)

        st.session_state.auth_mode = "login"
        st.rerun()


# =============================================================
# FORGOT PASSWORD PAGE
# =============================================================

def _forgot_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
<div style="text-align:center; margin-bottom:24px;">
  <h1 style="font-size:24px; font-weight:600; color:#ececec; margin:0;">
    Reset password
  </h1>
  <p style="font-size:13px; color:#8e8ea0; margin-top:6px;">
    Enter your email and we will send a reset link
  </p>
</div>
""", unsafe_allow_html=True)

        email = st.text_input("Email address", placeholder="you@example.com")
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("Send reset link", key="btn_send_reset"):
            user = get_user(email)
            if user and user.get("role") != "admin":
                token  = str(uuid.uuid4())
                expiry = datetime.now() + timedelta(hours=1)
                update_reset_token(email, token, expiry)
                send_reset_email(email, token)
                st.success("📧 Reset link sent! Please check your inbox.")
            else:
                # Don't reveal whether the email exists
                st.info("If that email is registered, a reset link has been sent.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to login", key="btn_back_forgot"):
            st.session_state.auth_mode = "login"
            st.rerun()


# =============================================================
# RESET PASSWORD PAGE
# =============================================================

def _reset_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
<div style="text-align:center; margin-bottom:24px;">
  <h1 style="font-size:24px; font-weight:600; color:#ececec; margin:0;">
    Set new password
  </h1>
</div>
""", unsafe_allow_html=True)

        token   = st.session_state.get("reset_token")
        new_pw  = st.text_input("New password",    type="password",
                                placeholder="Minimum 8 characters")
        confirm = st.text_input("Confirm password", type="password",
                                placeholder="Repeat your new password")
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("Reset password", key="btn_reset"):
            if not token:
                st.error("❌ Invalid or missing reset link.")
            elif len(new_pw) < 8:
                st.error("❌ Password must be at least 8 characters.")
            elif new_pw != confirm:
                st.error("❌ Passwords do not match.")
            else:
                # Store raw password for testing purposes
                hashed = new_pw
                if reset_user_password_by_token(token, hashed):
                    st.success("✅ Password updated! Redirecting to login…")
                    time.sleep(1.5)
                    st.session_state.auth_mode = "login"
                    st.session_state.pop("reset_token", None)
                    st.rerun()
                else:
                    st.error("❌ This reset link is invalid or has expired.")
        st.markdown('</div>', unsafe_allow_html=True)
