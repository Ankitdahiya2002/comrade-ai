# =============================================================
# app.py  —  Wingman AI
# Main entry point. Renders the full application.
#
# Flow:
#   1. Not logged in  → auth_page()     (src/auth.py)
#   2. Admin login    → show_admin_panel() (src/admin.py)
#   3. User login     → show_user_panel()  (this file)
# =============================================================

import base64
import time

import streamlit as st

from src.db import (
    safe_initialize,
    get_user,
    get_user_chats,
    save_chat,
    get_uploaded_files,
    save_uploaded_file,
    delete_user_chats,
    create_project,
    get_user_projects,
    delete_project,
)
from src.auth  import auth_page, verify_user_token
from src.admin import show_admin_panel
from src.helper import (
    ai_chat_response,
    is_image_request,
    generate_image,
)
from src.file_reader import extract_file


# =============================================================
# PAGE CONFIG  — must be the first Streamlit call
# =============================================================

st.set_page_config(
    page_title="Comrade Ai",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================


# Initialise the database tables on every cold start
safe_initialize()


# =============================================================
# SESSION STATE DEFAULTS
# =============================================================

_DEFAULTS = {
    "user":             None,   # logged-in user's email
    "user_role":        None,   # "user" or "admin"
    "theme":            "dark", # "dark" or "light"
    "model":            "claude",
    "active_file_name": None,   # name of the currently loaded file
    "active_file_text": None,   # extracted text of the loaded file
    "show_welcome":     True,   # show "Ready when you are" on first open
    "pending_prompt":   "",     # pre-filled prompt from a recommendation card
    # Auth state — must be initialised before auth_page() is called
    "auth_mode":        "landing",
    "auth_role":        "user",
    "prefill_email":    "",
    "otp_phone":        "",
    "otp_sent":         False,
    # Sidebar features
    "active_project_id":      None,
    "sidebar_search_query":   "",
    "show_sidebar_search":    False,
    "show_new_project_input": False,
    # Chat filter — which conversation is selected from sidebar
    "active_chat_filter":     None,
    "active_chat_id":          None,
}

for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =============================================================
# THEME CSS  — professional dark / light, ChatGPT-style
# =============================================================

def _apply_theme_css(img_b64="", bg_b64="", is_admin: bool = False):
    """
    Inject all CSS into the page.
    Propagates the premium Comrade AI theme to the main app dashboard.
    """
    dark = True # Main app is always dark for premium consistency
    
    # Success Cyan Theme for the Main App
    GLOW = "rgba(6, 182, 212, 0.6)"
    TINT = "rgba(6, 182, 212, 0.15)"
    PRI  = "#06b6d4"

    # Colour tokens
    BG       = "#0a0a0f" if dark else "#f5f5fb"
    BG2      = "#0d0d14" if dark else "#ebebf5"
    BG3      = "#16161f" if dark else "#e0e0ec"
    BORDER   = "rgba(255,255,255,0.08)" if dark else "rgba(0,0,0,0.08)"
    TX       = "#e8e6f0" if dark else "#12101f"
    TX2      = "rgba(200,200,220,0.55)" if dark else "rgba(30,20,60,0.5)"
    BUB_U    = "linear-gradient(135deg, #1e1e2e 0%, #232334 100%)" if dark else "linear-gradient(135deg, #e8e8f8 0%, #f0f0ff 100%)"
    BUB_AI   = "#0f0f17" if dark else "#ffffff"
    AI_BORDER= "#19c37d"
    INPUT_BG = "rgba(255,255,255,0.04)" if dark else "rgba(0,0,0,0.03)"
    INPUT_BD = "rgba(255,255,255,0.1)" if dark else "rgba(0,0,0,0.1)"
    ACCENT   = "#19c37d"
    GLOW_GRN = "rgba(25,195,125,0.15)"
    GLOW_PRP = "rgba(83,70,218,0.12)"

    # Inject Google Fonts separately to avoid Streamlit HTML parser issues
    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">',
        unsafe_allow_html=True
    )
    st.markdown(f"""
<style>

/* ── Base + all containers ── */
[data-testid="stAppViewContainer"] {{
    background: #020617 !important;
    background-image: 
        url("data:image/png;base64,{bg_b64 if bg_b64 else img_b64}"),
        radial-gradient(circle at center, {GLOW}, transparent 80%),
        linear-gradient({TINT}, rgba(2, 6, 23, 0.98)) !important;
    background-size: cover !important;
    background-position: center center !important;
    background-attachment: fixed !important;
    color: #ffffff !important;
}}

[data-testid="stMainBlockContainer"],
[data-testid="stMain"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
.main {{
    background: transparent !important;
    color: #ffffff !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    transition: background 0.4s ease, color 0.3s ease;
}}
[data-testid="block-container"],
.block-container {{
    padding: 1rem !important;
}}

/* ── Sidebar Navigation Toggle (Keep Visible) ── */
header {{ background: transparent !important; }}
[data-testid="stHeader"] {{ background: transparent !important; }}
.stAppDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stSidebarCollapseButton"] {{
    height: 0.75rem !important;
    min-height: 24px !important;
}}

/* ── Columns and expanders ── */
[data-testid="column"] {{
    background: transparent !important;
}}
[data-testid="stExpander"] {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
}}

/* ── Welcome Screen Typrography ── */
.welcome-title {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 4rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    background: linear-gradient(135deg, #ffffff 0%, {PRI} 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin-bottom: 0.5rem !important;
    text-align: center !important;
    margin-top: 0rem !important;
}}
.welcome-sub {{
    font-family: 'Inter', sans-serif !important;
    font-size: 1.5rem !important;
    font-weight: 300 !important;
    color: {TX2} !important;
    text-align: center !important;
    letter-spacing: 0.5em !important;
    text-transform: uppercase !important;
    margin-top: 1rem;
}}

/* ── Animated Hero UFO ── */
@keyframes floatUfo {{
    0% {{ transform: translateY(0) rotate(0deg) scale(1); filter: drop-shadow(0 0 20px {PRI}44); }}
    25% {{ transform: translateY(-20px) rotate(90deg) scale(1.05); filter: drop-shadow(0 0 40px {PRI}66); }}
    50% {{ transform: translateY(0) rotate(180deg) scale(1); filter: drop-shadow(0 0 20px {PRI}44); }}
    75% {{ transform: translateY(20px) rotate(270deg) scale(0.95); filter: drop-shadow(0 0 40px {PRI}66); }}
    100% {{ transform: translateY(0) rotate(360deg) scale(1); filter: drop-shadow(0 0 20px {PRI}44); }}
}}
.hero-ufo-container {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 4rem 0;
    perspective: 1000px;
}}
.hero-ufo {{
    width: 280px;
    animation: floatUfo 12s infinite linear;
    filter: drop-shadow(0 0 20px {PRI}44);
    pointer-events: none;
    transform-style: preserve-3d;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child {{
    background: rgba(15, 23, 42, 0.7) !important;
    border-right: 1px solid {PRI}44 !important;
    backdrop-filter: blur(25px) !important;
    box-shadow: 10px 0 30px rgba(2, 6, 23, 0.5);
    padding-top: 1rem !important;
    padding-bottom: 0rem !important;
}}
[data-testid="stSidebar"] * {{ color: {TX} !important; }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    gap: 0rem !important;
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
    padding: 0 !important;
    margin: 0 !important;
}}
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {{
    padding-top: 0 !important;
    padding-bottom: 0.1rem !important;
}}
[data-testid="stSidebar"] hr {{
    margin: 5px 0 !important;
    border-color: rgba(255,255,255,0.07) !important;
}}
/* Section header captions */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #8e8ea0 !important;
    padding: 10px 10px 2px 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}
/* Flex spacer */
[data-testid="stSidebar"] div:has(> .sidebar-flex-spacer) {{
    flex-grow: 1 !important;
    min-height: 1px !important;
}}
/* Sidebar Sticky Fixed Bottom Wrapper */
.sidebar-bottom-sticky {{
    position: fixed;
    bottom: 0px !important;
    left: 0px !important;
    width: 250px !important; /* Fixed width of the sidebar nav container */
    z-index: 1000;
    background: rgba(15, 23, 42, 0.98);
    backdrop-filter: blur(20px);
    padding: 12px 15px 12px 15px !important;
    border-top: 1px solid rgba(255,255,255,0.07);
}}
.sidebar-footer-link {{
    text-decoration: none !important;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px !important;
    color: {TX2} !important;
    padding: 6px 0;
    transition: color 0.2s;
}}
.sidebar-footer-link:hover {{
    color: #ffffff !important;
}}
@media (max-width: 768px) {{
    .sidebar-bottom-sticky {{ width: 100%; }}
}}
/* Project item row */
.project-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
}}
.project-row .stButton > button {{
    flex-grow: 1 !important;
}}
/* ── STICKY BOTTOM INPUT BAR ── */
[data-testid="stVerticalBlock"] > div:has(.chat-spacer) {{
    position: fixed !important;
    bottom: 0 !important;
    left: 336px !important; /* Standard Streamlit sidebar width */
    width: calc(100% - 336px) !important;
    background: #0a0a0f !important;
    z-index: 999 !important;
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}}

/* For mobile / collapsed sidebar */
[data-testid="stSidebar"][aria-expanded="false"] + section [data-testid="stVerticalBlock"] > div:has(.chat-spacer) {{
    left: 0 !important;
    width: 100% !important;
}}

.chat-spacer {{ height: 0px !important; display: none; }}
.project-delete-btn .stButton > button {{
    width: 28px !important;
    min-width: 28px !important;
    height: 28px !important;
    padding: 0 !important;
    font-size: 14px !important;
    color: #555 !important;
    background: transparent !important;
    border: none !important;
}}
.project-delete-btn .stButton > button:hover {{
    color: #ff4b4b !important;
    background: rgba(255,0,0,0.05) !important;
}}

/* Search text input */
[data-testid="stSidebar"] [data-testid="stTextInput"] {{
    padding: 0 4px !important;
}}
[data-testid="stSidebar"] [data-testid="stTextInput"] input {{
    background: #202123 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 6px !important;
    color: #ececec !important;
    font-size: 12px !important;
    padding: 4px 10px !important;
}}
/* ── ALL sidebar buttons base ── */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    color: #c5c5d2 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 5px 10px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
    font-weight: 400 !important;
    line-height: 1.35 !important;
    transition: background 0.1s ease !important;
    width: 100% !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.06) !important;
    color: #ececec !important;
    transform: none !important;
    box-shadow: none !important;
    border-color: transparent !important;
}}
/* Nav buttons - New chat, Search chats, New project */
.sidebar-nav-btn .stButton > button {{
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #ededf0 !important;
    padding: 5px 10px !important;
}}
/* Small button override for Clear History */
.small-btn .stButton > button {{
    font-size: 10.5px !important;
    padding: 2px 8px !important;
    color: #8e8ea0 !important;
    height: 26px !important;
    min-height: 26px !important;
}}
/* Chat history list items — smaller/medium */
.sidebar-hist-btn .stButton > button {{
    font-size: 11.5px !important;
    font-weight: 400 !important;
    color: #a0a0b8 !important;
    padding: 3px 10px !important;
}}
.sidebar-hist-btn .stButton > button:hover {{
    color: #dddde8 !important;
    background: rgba(255,255,255,0.04) !important;
}}
/* Active selected chat */
.sidebar-hist-active .stButton > button {{
    background: rgba(25,195,125,0.08) !important;
    color: #19c37d !important;
    font-weight: 500 !important;
    font-size: 11.5px !important;
    padding: 3px 10px !important;
}}
/* Active project */
.sidebar-proj-active .stButton > button {{
    background: rgba(83,70,218,0.12) !important;
    color: #a89ff0 !important;
    font-weight: 500 !important;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer,
.stDeployButton {{ display: none !important; }}

/* ── Main Panel buttons — base style ── */
[data-testid="stMainBlockContainer"] .stButton > button {{
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid {BORDER} !important;
    color: {TX} !important;
    border-radius: 10px !important;
    font-size: 13.5px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 9px 16px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
}}
[data-testid="stMainBlockContainer"] .stButton > button:hover {{
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(25,195,125,0.35) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px {GLOW_GRN} !important;
}}
[data-testid="stMainBlockContainer"] .stButton > button:active {{
    transform: translateY(0px) !important;
}}

/* ── Chat Model Indicator (inside bar) ── */
.chat-model-indicator {{
    position: absolute;
    left: 45px; /* Offset to stay next to the + icon at 18px */
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #8e8ea0 !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    padding: 3px 8px !important;
    border-radius: 6px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    z-index: 10;
    pointer-events: none;
}}
/* Adjust input padding for model chip, without relying on the removed anchor */
.stTextInput input {{
    padding-left: {"115px" if is_admin else "50px"} !important;
}}

/* ── Popover Trigger (Attach File) ── */
[data-testid="stPopover"] > button {{
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(25,195,125,0.3) !important;
    color: {TX2} !important;
    border-radius: 12px !important;
    padding: 9px 16px !important;
    transition: all 0.2s ease !important;
    font-size: 13px !important;
    width: 100% !important;
}}
[data-testid="stPopover"] > button:hover {{
    background: {GLOW_GRN} !important;
    border-color: rgba(25,195,125,0.6) !important;
    color: {ACCENT} !important;
}}

/* ── Neon green primary button ── */
.primary-btn .stButton > button {{
    background: linear-gradient(135deg, {ACCENT} 0%, #0fa86a 100%) !important;
    border-color: transparent !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 24px rgba(25,195,125,0.35) !important;
}}
.primary-btn .stButton > button:hover {{
    box-shadow: 0 8px 36px rgba(25,195,125,0.55), 0 0 0 4px rgba(25,195,125,0.12) !important;
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #1fd88c 0%, #14b874 100%) !important;
    border-color: transparent !important;
}}

/* ── Text inputs (ChatGPT Searchbox Style) ── */
.stTextInput > div > div > input {{
    background: #212121 !important; /* ChatGPT dark gray */
    border: none !important;
    border-radius: 30px !important;
    color: #ececec !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 16px 80px 16px 50px !important; /* Spacing for the + and mic/voice icons */
    transition: all 0.2s ease !important;
}}
.stTextInput > div > div {{
    background: transparent !important;
    border: none !important;
    position: relative;
}}
.stTextInput > div > div > input::placeholder {{
    color: #8e8ea0 !important;
}}
.stTextInput > div > div > input:focus {{
    box-shadow: 0 0 0 2px rgba(255,255,255,0.1) !important;
}}

/* ── Pseudo-icons to mimic the ChatGPT UI ── */
.stTextInput > div::before {{
    content: "＋";
    position: absolute;
    left: 18px;
    top: 50%;
    transform: translateY(-50%);
    color: #ececec;
    font-size: 20px;
    font-weight: 300;
    z-index: 10;
    pointer-events: none;
    opacity: 0.8;
}}
.stTextInput > div::after {{
    /* Mic and Voice indicator imitating the screenshot closely */
    content: " \\00a0 ";
    position: absolute;
    right: 18px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 16px;
    z-index: 10;
    pointer-events: none;
    opacity: 0.9;
}}

/* ── Radio buttons (model selector) ── */
.stRadio > div {{ flex-direction: row !important; gap: 8px !important; }}
.stRadio label {{
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid {BORDER} !important;
    border-radius: 20px !important;
    padding: 5px 16px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    color: {TX2} !important;
    transition: all 0.2s ease !important;
}}
.stRadio label:has(input:checked) {{
    background: rgba(25,195,125,0.14) !important;
    border-color: rgba(25,195,125,0.45) !important;
    color: {ACCENT} !important;
}}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px dashed rgba(25,195,125,0.25) !important;
    border-radius: 14px !important;
    transition: all 0.2s ease !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: rgba(25,195,125,0.45) !important;
    background: rgba(25,195,125,0.03) !important;
}}
[data-testid="stFileUploader"] * {{ color: {TX2} !important; }}

/* ── Divider ── */
hr {{ border-color: {BORDER} !important; }}

/* ── Chat bubbles ── */
.user-bubble {{
    background: {BUB_U};
    color: {TX};
    padding: 13px 20px;
    border-radius: 20px 20px 5px 20px;
    display: inline-block;
    max-width: 78%;
    font-size: 14px;
    line-height: 1.65;
    float: right;
    clear: both;
    margin-bottom: 3px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}}
.ai-bubble {{
    background: {BUB_AI};
    color: {TX};
    padding: 16px 20px;
    border-radius: 20px 20px 20px 5px;
    border-left: 3px solid {AI_BORDER};
    box-shadow: -2px 0 20px rgba(25,195,125,0.08), 0 4px 20px rgba(0,0,0,0.15);
    display: block;
    max-width: 88%;
    font-size: 14px;
    line-height: 1.75;
    float: left;
    clear: both;
    margin-bottom: 3px;
}}
.ai-bubble ul {{ padding-left: 20px; margin: 8px 0; }}
.ai-bubble li {{ margin-bottom: 6px; color: {TX2}; }}
.ai-bubble li strong {{ color: {TX}; }}
.ai-bubble h4 {{ font-size: 15px; font-weight: 600; margin-bottom: 8px; font-family: 'Space Grotesk', sans-serif; }}
.ai-bubble code {{
    display: block;
    background: #050508;
    color: {ACCENT};
    padding: 14px 18px;
    border-radius: 10px;
    border: 1px solid rgba(25,195,125,0.15);
    font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
    font-size: 12.5px;
    white-space: pre;
    overflow-x: auto;
    margin: 10px 0;
}}
.bubble-wrap {{ overflow: hidden; margin-bottom: 4px; }}
.msg-timestamp {{
    font-size: 10px;
    color: {TX2};
    clear: both;
    display: block;
    padding: 0 4px 12px;
}}
.msg-right {{ text-align: right; }}
.msg-left  {{ text-align: left; }}
.model-label {{
    font-size: 10px;
    color: {TX2};
    display: block;
    margin-top: 2px;
}}

/* ── File context banner ── */
.file-banner {{
    background: {'rgba(25,195,125,0.07)' if dark else 'rgba(25,195,125,0.06)'};
    border: 1px solid rgba(25,195,125,0.2);
    border-radius: 12px;
    padding: 9px 16px;
    font-size: 12px;
    color: {'#9FE1CB' if dark else '#0F6E56'};
    margin-bottom: 12px;
    box-shadow: 0 0 20px rgba(25,195,125,0.05);
}}

/* ── Welcome title ── */
.welcome-title {{
    font-size: 36px;
    font-weight: 700;
    font-family: 'Space Grotesk', sans-serif;
    color: {TX};
    text-align: center;
    letter-spacing: -1px;
    margin-bottom: 8px;
    background: linear-gradient(135deg, {TX} 0%, {ACCENT} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.welcome-sub {{
    font-size: 16.5px;
    background: linear-gradient(135deg, {TX} 0%, {ACCENT} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 32px;
    letter-spacing: 0.05em;
    font-weight: 600;
}}

/* ── Recommendation cards ── */
.rec-card {{
    background: {'rgba(255,255,255,0.04)' if dark else 'rgba(0,0,0,0.03)'};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 16px 18px;
    cursor: pointer;
    min-height: 80px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(8px);
}}
.rec-card:hover {{
    background: rgba(25,195,125,0.07) !important;
    border-color: rgba(25,195,125,0.3) !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(25,195,125,0.1);
}}
.rc-title {{ font-size: 13px; font-weight: 600; color: {TX}; font-family: 'Space Grotesk', sans-serif; }}
.rc-sub   {{ font-size: 11.5px; color: {TX2}; margin-top: 5px; }}

/* ── Footer disclaimer ── */
.chat-footer {{
    text-align: center;
    padding: 10px 0 5px;
    font-size: 11px;
    color: rgba(200,200,220,0.3) !important;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.01em;
}}
[data-testid="stFooter"] {{ visibility: hidden; height: 0px !important; }}

/* ── Divider — hide the ugly default hr ── */
hr {{
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    margin: 0.5rem 0 !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {'rgba(255,255,255,0.1)' if dark else 'rgba(0,0,0,0.12)'}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(25,195,125,0.45); }}

/* ── Alerts ── */
.stAlert {{ border-radius: 12px !important; backdrop-filter: blur(8px) !important; }}

/* ── Sidebar user avatar ── */
.user-avatar {{
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #5436da 0%, #19c37d 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700; color: #fff;
    flex-shrink: 0;
    box-shadow: 0 0 12px rgba(83,70,218,0.35);
}}

/* ── Message input bar — ChatGPT pill look ── */
[data-testid="stMainBlockContainer"] .stTextInput > div > div > input {{
    background: #1e1e2e !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 30px !important;
    color: #ececec !important;
    -webkit-text-fill-color: #ececec !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 16px 80px 16px 50px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
[data-testid="stMainBlockContainer"] .stTextInput > div > div > input:focus {{
    border-color: rgba(25,195,125,0.4) !important;
    box-shadow: 0 0 0 3px rgba(25,195,125,0.08) !important;
    background: #1e1e2e !important;
}}
[data-testid="stMainBlockContainer"] .stTextInput > div > div > input::placeholder {{
    color: #8e8ea0 !important;
}}

/* ── Sticky chat bar container ── */
[data-testid="stVerticalBlock"] > div:has(.chat-spacer) {{
    position: fixed !important;
    bottom: 0 !important;
    left: 336px !important;
    width: calc(100% - 336px) !important;
    background: linear-gradient(to top, #0a0a0f 60%, transparent) !important;
    z-index: 999 !important;
    padding: 16px 24px 12px !important;
}}
[data-testid="stSidebar"][aria-expanded="false"] + section [data-testid="stVerticalBlock"] > div:has(.chat-spacer) {{
    left: 0 !important;
    width: 100% !important;
}}
.chat-spacer {{ height: 130px; display: block !important; }}

/* ── Footer ── */
.chat-footer {{
    text-align: center;
    padding: 8px 0 2px;
    font-size: 11px;
    color: rgba(200,200,220,0.25) !important;
    font-family: 'Inter', sans-serif;
}}
[data-testid="stFooter"] {{ visibility: hidden; height: 0px !important; }}

</style>
""", unsafe_allow_html=True)


# =============================================================
# SIDEBAR
# =============================================================

def _render_sidebar(user_email: str, user_name: str):
    """Render the left sidebar with navigation and chat history."""

    with st.sidebar:

        # ── Logo ──────────────────────────────────────────────
        st.markdown('<div class="sidebar-nav-btn">', unsafe_allow_html=True)
        if st.button("🪐 Comrade Ai", key="home_logo", use_container_width=True):
            _reset_to_welcome()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Navigation ────────────────────────────────────────
        if st.button("🛫  New chat", key="new_chat", use_container_width=True):
            st.session_state.active_chat_id = None
            st.session_state.show_welcome     = True
            st.session_state.active_file_name = None
            st.session_state.active_file_text = None
            st.rerun()

        if st.button("🔍  Search chats", key="btn_search_toggle", use_container_width=True):
            st.session_state.show_sidebar_search = not st.session_state.show_sidebar_search
            st.rerun()

        if st.session_state.show_sidebar_search:
            st.session_state.sidebar_search_query = st.text_input("Search", placeholder="Type to filter chats...", label_visibility="collapsed")

        # ── Projects ──────────────────────────────────────
        st.caption("Projects")
        
        if st.button("📁  New project", key="btn_new_proj_toggle", use_container_width=True):
            st.session_state.show_new_project_input = not st.session_state.show_new_project_input
            st.rerun()
            
        if st.session_state.show_new_project_input:
            new_proj_name = st.text_input("Project name", placeholder="Press enter to create", label_visibility="collapsed", key="new_proj_input")
            if new_proj_name:
                p = create_project(user_email, new_proj_name)
                st.session_state.active_project_id = p["id"] if p else None
                st.session_state.active_chat_filter = None
                st.session_state.show_new_project_input = False
                _reset_to_welcome()

        projects = get_user_projects(user_email)
        for proj in projects:
            is_active = (st.session_state.active_project_id == proj["id"])
            icon = "📂" if is_active else "📁"
            label = f"{icon}  {proj['name']}"
            if is_active:
                label += "  ✓"
            
            # Project Row with Delete Dots
            col_p, col_d = st.columns([5, 1])
            with col_p:
                if is_active: st.markdown('<div class="sidebar-proj-active">', unsafe_allow_html=True)
                if st.button(label, key=f"proj_{proj['id']}", use_container_width=True):
                    if is_active:
                        st.session_state.active_project_id = None
                    else:
                        st.session_state.active_project_id = proj['id']
                    st.rerun()
                if is_active: st.markdown('</div>', unsafe_allow_html=True)
                
            with col_d:
                st.markdown('<div class="project-delete-btn">', unsafe_allow_html=True)
                if st.button("⋮", key=f"del_dots_{proj['id']}", help="Delete Project"):
                    delete_project(proj["id"])
                    if st.session_state.active_project_id == proj["id"]:
                        st.session_state.active_project_id = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Chat history ──────────────────────────────────────
        st.caption("Your chats")

        all_chats = get_user_chats(user_email, st.session_state.active_project_id)
        
        if all_chats:
            st.markdown('<div class="small-btn">', unsafe_allow_html=True)
            if st.button("🧹  Clear history", key="clear_hist", use_container_width=True):
                delete_user_chats(user_email)
                _reset_to_welcome()
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.sidebar_search_query:
            q = st.session_state.sidebar_search_query.lower()
            chats = [c for c in all_chats if q in c.get("user_input", "").lower() or q in c.get("ai_response", "").lower()]
        else:
            chats = all_chats

        # Group into conversations
        # dict: { conversation_id: { 'title': str, 'ts': str } }
        conv_map = {}
        for chat in all_chats:
            cid = chat.get("conversation_id")
            if not cid:
                cid = "legacy_" + str(chat["id"]) # Handle older messages
                
            # If we haven't seen this CID yet, it's the "latest" one for it (since all_chats is DESC)
            if cid not in conv_map:
                conv_map[cid] = {
                    "title": chat["user_input"][:45],
                    "ts":    str(chat.get("timestamp", ""))[:19],
                    "id":    cid
                }
        
        # Sort conversations by timestamp DESC
        history = sorted(conv_map.values(), key=lambda x: x["ts"], reverse=True)

        for item in history[:15]:
            # Convert timestamp to IST for display
            try:
                from datetime import datetime, timedelta
                dt_str = item["ts"].replace(' ', 'T')
                dt = datetime.fromisoformat(dt_str)
                ist_dt = dt + timedelta(hours=5, minutes=30)
                display_ts = ist_dt.strftime("%b %d, %H:%M")
            except:
                display_ts = item["ts"][:10]
                
            label  = item["title"] + ("…" if len(item["title"]) == 45 else "")
            is_active = st.session_state.active_chat_id == item["id"]
            
            # Highlight active conversation
            btn_style = "border-left: 3px solid #19c37d !important; background: rgba(25,195,125,0.05) !important;" if is_active else ""
            
            if st.button(label, key=f"conv_{item['id']}", use_container_width=True, help=display_ts):
                st.session_state.active_chat_id = item["id"]
                st.session_state.show_welcome   = False
                st.rerun()

        # ── Flex spacer pushes bottom section down ────────────
        st.markdown('<div class="sidebar-flex-spacer" style="min-height:50px;"></div>', unsafe_allow_html=True)

        # ── Sticky Fixed bottom ──────────────────────────────────────
        st.markdown('<div class="sidebar-bottom-sticky">', unsafe_allow_html=True)

        # User card
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;">
  <div class="user-avatar" style="width:30px;height:30px;border-radius:50%;background:#19c37d;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;">{user_name[:2].upper()}</div>
  <div>
    <div style="font-size:13px;font-weight:600;font-family:'Space Grotesk',sans-serif;">{user_name}</div>
    <div style="font-size:11px;color:rgba(25,195,125,0.65);font-weight:500;">Free Plan</div>
  </div>
</div>
""", unsafe_allow_html=True)

        if st.button("⭐  Upgrade to Pro (Coming Soon)", key="upgrade", use_container_width=True):
            pass

        if st.button("🔒  Logout", key="logout", use_container_width=True):
            for key in _DEFAULTS:
                st.session_state[key] = _DEFAULTS[key]
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)


def _reset_to_welcome():
    """Clear the active session and return to the welcome screen."""
    st.session_state.show_welcome    = True
    st.session_state.active_file_name = None
    st.session_state.active_file_text = None
    st.session_state.pending_prompt   = ""
    st.session_state.active_chat_filter = None
    st.rerun()


# Recommendations removed per user request


# =============================================================
# CHAT MESSAGE RENDERING
# =============================================================


# =============================================================
# CHAT MESSAGE RENDERING
# =============================================================

def _render_chat_messages(chats: list[dict]):
    """Render the full conversation as styled bubbles."""
    for chat in chats:
        # Convert UTC to IST (+5:30)
        try:
            from datetime import datetime, timedelta
            raw_ts = chat.get("timestamp", "")
            dt = datetime.fromisoformat(raw_ts.replace(' ', 'T')) if ' ' in str(raw_ts) else datetime.fromisoformat(str(raw_ts))
            ist_dt = dt + timedelta(hours=5, minutes=30)
            ts = ist_dt.strftime("%b %d, %H:%M")
        except:
            ts = str(chat.get("timestamp", ""))[:16]

        model_used  = chat.get("model", "claude")
        model_label = "Claude Sonnet 4" if model_used == "claude" else "Gemini 2.5 Flash"

        # User bubble (right-aligned)
        st.markdown(
            f'<div class="bubble-wrap">'
            f'<div class="user-bubble">{chat["user_input"]}</div>'
            f'</div>'
            f'<span class="msg-timestamp msg-right">{ts}</span>',
            unsafe_allow_html=True,
        )

        # AI bubble (left-aligned)
        # Convert newlines to <br> so multi-line responses display correctly
        response = chat["ai_response"].replace("\n", "<br>")
        
        # Determine if we show the model label (only for admins)
        user_email = st.session_state.get("user")
        from src.db import get_user
        user = get_user(user_email) if user_email else None
        show_model = user and user.get("role") == "admin"
        
        model_display = f"{model_label} · " if show_model else ""
        
        st.markdown(
            f'<div class="bubble-wrap">'
            f'<div class="ai-bubble">{response}</div>'
            f'</div>'
            f'<span class="model-label">{model_display}{ts}</span>',
            unsafe_allow_html=True,
        )

        # Copy button under each AI reply
        st.button("📋 Copy response", key=f"copy_{chat.get('id', ts)}")


# =============================================================
# MAIN USER PANEL
# =============================================================

def show_user_panel():
    """Render the full chat UI for a logged-in user."""
    user_email = st.session_state.user
    user       = get_user(user_email) or {}
    user_name  = user.get("name", "User")
    is_admin   = user.get("role") == "admin"
    
    # Load assets for premium theme propagation
    from src.auth import _get_base64_image
    import os
    img_path = os.path.join(os.path.dirname(__file__), "assets", "banner.png")
    img_b64 = _get_base64_image(img_path)
    bg_path = os.path.join(os.path.dirname(__file__), "assets", "background.png")
    bg_b64  = _get_base64_image(bg_path)
    
    _apply_theme_css(img_b64, bg_b64, is_admin)

    _render_sidebar(user_email, user_name)

    chats = get_user_chats(user_email, st.session_state.active_project_id)

    # If a specific chat is selected from the sidebar, filter messages
    if st.session_state.active_chat_filter:
        chats = [c for c in chats if c.get("user_input", "").startswith(st.session_state.active_chat_filter)]

    # ── Welcome screen or chat history ────────────────────────
    # Show welcome ONLY if there is no active chat selected
    if st.session_state.active_chat_id is None or st.session_state.show_welcome:
        st.markdown('<div class="welcome-title">Welcome to ComradeAi</div>',
                    unsafe_allow_html=True)
        
        # Animated Hero UFO (with fallback to emoji if image is missing)
        if img_b64:
            st.markdown(f"""
                <div class="hero-ufo-container">
                    <img src="data:image/png;base64,{img_b64}" class="hero-ufo" alt="🛸">
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="hero-ufo-container">
                    <div class="hero-ufo" style="font-size: 8rem; display: flex; justify-content: center; align-items: center;">🛸</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown(
            '<div class="welcome-sub">👋🏻hello!</div>',
            unsafe_allow_html=True,
        )
    else:
        # Filter all_chats by the active session ID
        active_chats = [c for c in chats if c.get("conversation_id") == st.session_state.active_chat_id or 
                       (not c.get("conversation_id") and st.session_state.active_chat_id == "legacy_" + str(c["id"]))]
        
        # We want the bubbles chronologically for a specific conversation
        _render_chat_messages(sorted(active_chats, key=lambda x: x["timestamp"]))

    st.markdown("---")

    # ── File context banner (shown when a file is loaded) ─────
    if st.session_state.active_file_name:
        col_banner, col_clear = st.columns([9, 1])
        with col_banner:
            words = len((st.session_state.active_file_text or "").split())
            st.markdown(
                f'<div class="file-banner">'
                f'📄 <strong>{st.session_state.active_file_name}</strong>'
                f' &nbsp;·&nbsp; {words:,} words · AI will answer using this file'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_clear:
            if st.button("✕", key="clear_file"):
                st.session_state.active_file_name = None
                st.session_state.active_file_text = None
                st.rerun()

    # ── FIXED BOTTOM CHAT CONTROLS ────────────────────────────
    bottom_container = st.container()
    with bottom_container:
        # ── Model selector + file uploader (same row) ─────────────
        if is_admin:
            col_model, col_spacer, col_upload = st.columns([5, 3, 2])
            with col_model:
                with st.popover(f"Model: {st.session_state.model.title()}  ", use_container_width=True):
                    new_model = st.radio(
                        "Switch AI Model",
                        options=["claude", "gemini"],
                        format_func=lambda x: "✦ Claude Sonnet 4" if x == "claude" else "◆ Gemini 2.5 Flash",
                        index=0 if st.session_state.model == "claude" else 1,
                        key="pop_model_select"
                    )
                    if new_model != st.session_state.model:
                        st.session_state.model = new_model
                        st.rerun()
        else:
            col_spacer, col_upload = st.columns([8, 2])

        with col_upload:
            with st.popover("📎 Attach File", use_container_width=True):
                uploaded = st.file_uploader(
                    "Upload document",
                    type=["pdf", "txt", "xlsx", "xls", "csv"],
                    label_visibility="collapsed",
                    key="file_uploader",
                )
                if uploaded and uploaded.name != st.session_state.active_file_name:
                    with st.spinner("Reading…"):
                        try:
                            text = extract_file(uploaded)
                            save_uploaded_file(
                                user_email, uploaded.name, uploaded.type, text
                            )
                            st.session_state.active_file_name = uploaded.name
                            st.session_state.active_file_text = text
                            st.success(f"✅ {len(text.split()):,} words ready.")
                        except Exception as e:
                            st.error(f"❌ {e}")

        # ── Message input area ─────────────────────────────────

        # ── Message input (Enter to send) ─────────────────────────
        if is_admin:
            st.markdown(f'<div class="chat-model-indicator">{st.session_state.model}</div>', unsafe_allow_html=True)
        
        prefill = st.session_state.get("pending_prompt", "")
        if prefill:
            st.session_state.pending_prompt = ""  # Clear so it doesn't loop

        def _on_message_submit():
            text = st.session_state.message_input
            if text and text.strip():
                st.session_state.to_process = text.strip()
            # Clear input automatically
            st.session_state.message_input = ""

        # A single wide text input formatted via CSS as a ChatGPT pill
        st.text_input(
            "Message",
            value=prefill,
            placeholder="Ask anything",
            label_visibility="collapsed",
            key="message_input",
            on_change=_on_message_submit
        )

        st.markdown(
            '<div class="chat-footer">'
            'ComradeAi can make mistakes. Verify important information.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Handle the send action ────────────────────────────────
    if st.session_state.get("to_process"):
        msg_to_send = st.session_state.to_process
        st.session_state.to_process = ""
        _process_message(msg_to_send, user_email, chats)


def _process_message(text: str, user_email: str, chats: list[dict]):
    """
    Called when the user presses Send.
    Routes to image generation or regular chat as appropriate.
    """
    st.session_state.show_welcome = False

    # ── Image request ─────────────────────────────────────────
    if is_image_request(text):
        with st.spinner("🎨 Generating image…"):
            result = generate_image(text)

        if result.get("success") and result.get("image_b64"):
            img_bytes = base64.b64decode(result["image_b64"])
            st.image(img_bytes, caption=result.get("revised_prompt", text))
            ai_reply = f"🎨 Image generated! Prompt: _{result.get('revised_prompt', text)}_"
        else:
            # No Stability key — describe the image and give a prompt
            if result.get("error") == "no_key":
                ai_reply = (
                    f"Image generation needs a STABILITY_API_KEY in secrets.toml.\n\n"
                    f"Here is an optimised prompt you can use in Midjourney or DALL-E:\n\n"
                    f"**`{result.get('revised_prompt', text)}`**"
                )
            else:
                ai_reply = f"⚠️ Image generation failed: {result.get('error')}. Please try again."

        save_chat(user_email, text, ai_reply, model=st.session_state.model, project_id=st.session_state.active_project_id)
        st.rerun()
        return

    # ── Regular chat ──────────────────────────────────────────
    # Build conversation history (last 5 turns for context)
    history = "".join(
        f"User: {c['user_input']}\nAI: {c['ai_response']}\n\n"
        for c in chats[-5:]
    )
    prompt = history + f"User: {text}\nAI:"

    # Attach file context if a file is loaded
    file_contexts = []
    if st.session_state.active_file_text:
        file_contexts = [{
            "name": st.session_state.active_file_name,
            "text": st.session_state.active_file_text,
        }]

    # Assign or generate a conversation ID
    if st.session_state.active_chat_id is None:
        import uuid
        st.session_state.active_chat_id = str(uuid.uuid4())
        st.session_state.show_welcome = False

    with st.spinner(""):
        ai_reply = ai_chat_response(
            prompt,
            model_choice=st.session_state.model,
            file_contexts=file_contexts,
        )

    save_chat(
        user_email, 
        text, 
        ai_reply, 
        model=st.session_state.model, 
        project_id=st.session_state.active_project_id,
        conversation_id=st.session_state.active_chat_id
    )
    st.rerun()


# =============================================================
# MAIN ROUTER
# =============================================================

def main():
    """
    Application entry point.
    Decides which screen to show based on login state and role.
    """
    # Handle email-verification link in the URL
    verify_token = st.query_params.get("verify_token")
    if verify_token:
        t = verify_token[0] if isinstance(verify_token, list) else verify_token
        if verify_user_token(t):
            st.sidebar.success("✅ Email verified. You can now log in.")

    # Route based on login state
    if not st.session_state.user:
        # Not logged in → show the auth pages
        auth_page()
    else:
        user = get_user(st.session_state.user) or {}
        if user.get("role") == "admin":
            # Admin → dark admin panel
            show_admin_panel()
        else:
            # Regular user → main chat UI
            show_user_panel()


if __name__ == "__main__":
    main()
