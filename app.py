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
    page_title="Wingman AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
# FRAGMENT -> QUERY WORKAROUND (for Google OAuth)
# =============================================================
# Streamlit cannot natively read fragments (#access_token=...), 
# so we use a component to inject JS to convert it and reload.
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
    "auth_mode":        "login",
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
}

for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =============================================================
# THEME CSS  — professional dark / light, ChatGPT-style
# =============================================================

def _apply_theme_css():
    """
    Inject all CSS into the page.
    Colours adapt to the current theme (dark / light).
    """
    dark = st.session_state.theme == "dark"

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
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMainBlockContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
.main, .block-container {{
    background: {BG} !important;
    color: {TX} !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    transition: background 0.4s ease, color 0.3s ease;
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

/* ── Animated mesh gradient background ── */
[data-testid="stAppViewContainer"]::before {{
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 50% at 20% -10%, {GLOW_GRN} 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 85% 110%, {GLOW_PRP} 0%, transparent 55%);
    pointer-events: none;
    z-index: 0;
    animation: meshPulse 10s ease-in-out infinite alternate;
}}
@keyframes meshPulse {{
    from {{ opacity: 0.6; }}
    to   {{ opacity: 1.0; }}
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child {{
    background: {BG2} !important;
    border-right: 1px solid {BORDER} !important;
    backdrop-filter: blur(20px) !important;
}}
[data-testid="stSidebar"] * {{ color: {TX} !important; }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    gap: 0.05rem !important;
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
    padding: 0 !important;
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
    bottom: 0px;
    width: 17.5rem; /* Matches sidebar default responsive width better */
    z-index: 1000;
    background: #111111;
    padding: 10px 15px 20px 15px;
    border-top: 1px solid rgba(255,255,255,0.07);
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
    padding-left: 115px !important;
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
    font-size: 15px;
    color: {TX2};
    text-align: center;
    margin-bottom: 32px;
    letter-spacing: 0.01em;
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
    font-size: 11px;
    color: #aaa;
    padding-top: 10px;
    font-family: 'Inter', sans-serif !important;
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

/* ── Sticky Bottom Footer ── */
/* Targets the specific vertical block whose VERY FIRST element-container has the sticky anchor */
[data-testid="stVerticalBlock"]:has(> div.element-container:nth-child(1) #sticky-anchor) {{
    position: fixed !important;
    bottom: 20px !important; /* Slightly up from absolute bottom */
    z-index: 99999 !important;
    width: 100% !important;
    max-width: 48rem !important;
    background: transparent !important; /* Allow the bubbles/gradient to show */
    padding: 0 !important;
    margin-bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
}}
/* Inner container for background effect */
[data-testid="stVerticalBlock"]:has(> div.element-container:nth-child(1) #sticky-anchor) > div {{
    background: linear-gradient(180deg, rgba(10,10,15,0) 0%, rgba(10,10,15,1) 40%) !important;
    backdrop-filter: blur(12px) !important;
    padding: 20px 0 !important;
}}
.chat-spacer {{ height: 260px; }}

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
        if st.button("🤖 Wingman AI", key="home_logo", use_container_width=True):
            _reset_to_welcome()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

        # ── Navigation ────────────────────────────────────────
        if st.button("📝  New chat", key="new_chat", use_container_width=True):
            _reset_to_welcome()

        if st.button("🔍  Search chats", key="btn_search_toggle", use_container_width=True):
            st.session_state.show_sidebar_search = not st.session_state.show_sidebar_search
            st.rerun()

        if st.session_state.show_sidebar_search:
            st.session_state.sidebar_search_query = st.text_input("Search", placeholder="Type to filter chats...", label_visibility="collapsed")
            
        st.markdown("<br>", unsafe_allow_html=True)

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

        st.markdown("<br>", unsafe_allow_html=True)

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

        # Deduplicate
        seen, history = set(), []
        for chat in reversed(chats):
            title = chat["user_input"][:45]
            if title not in seen:
                seen.add(title)
                history.append({
                    "title": title,
                    "ts":    str(chat.get("timestamp", ""))[:10],
                })

        for item in history[:15]:
            label = item["title"] + ("…" if len(item["title"]) == 45 else "")
            if st.button(label, key=f"hist_{item['title'][:18]}_{item['ts']}", use_container_width=True, help=item["ts"]):
                st.session_state.show_welcome = False
                st.rerun()

        # ── Flex spacer pushes bottom section down ────────────
        st.markdown('<div class="sidebar-flex-spacer" style="min-height:50px;"></div>', unsafe_allow_html=True)

        # ── Sticky Fixed bottom ──────────────────────────────────────
        st.markdown('<div class="sidebar-bottom-sticky">', unsafe_allow_html=True)
        st.markdown('<hr style="border-color:rgba(255,255,255,0.07);margin:6px 0;">', unsafe_allow_html=True)

        # User card
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:6px 0;">
  <div class="user-avatar" style="width:30px;height:30px;border-radius:50%;background:#19c37d;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;">{user_name[:2].upper()}</div>
  <div>
    <div style="font-size:13px;font-weight:600;font-family:'Space Grotesk',sans-serif;">{user_name}</div>
    <div style="font-size:11px;color:rgba(25,195,125,0.65);font-weight:500;">Free Plan</div>
  </div>
</div>
""", unsafe_allow_html=True)

        if st.button("⭐  Upgrade to Pro", key="upgrade", use_container_width=True):
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
        ts          = str(chat.get("timestamp", ""))[:16]
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
        st.markdown(
            f'<div class="bubble-wrap">'
            f'<div class="ai-bubble">{response}</div>'
            f'</div>'
            f'<span class="model-label">{model_label} · {ts}</span>',
            unsafe_allow_html=True,
        )

        # Copy button under each AI reply
        st.button("📋 Copy response", key=f"copy_{chat.get('id', ts)}")


# =============================================================
# MAIN USER PANEL
# =============================================================

def show_user_panel():
    """Render the full chat UI for a logged-in user."""
    _apply_theme_css()

    user_email = st.session_state.user
    user       = get_user(user_email) or {}
    user_name  = user.get("name", "User")

    _render_sidebar(user_email, user_name)

    chats = get_user_chats(user_email, st.session_state.active_project_id)

    # If a specific chat is selected from the sidebar, filter messages
    if st.session_state.active_chat_filter:
        chats = [c for c in chats if c.get("user_input", "").startswith(st.session_state.active_chat_filter)]

    # ── Welcome screen or chat history ────────────────────────
    # Show welcome if manually requested, OR if there's no chat history at all for this view
    if st.session_state.show_welcome or not chats:
        st.markdown('<div class="welcome-title">Ready when you are.</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="welcome-sub">Powered by Claude Sonnet 4 &amp; Gemini 2.5 Flash</div>',
            unsafe_allow_html=True,
        )
    else:
        st.session_state.show_welcome = False
        _render_chat_messages(chats)

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
    # Add a spacer so the chat messages don't get hidden behind the sticky footer
    st.markdown('<div class="chat-spacer"></div>', unsafe_allow_html=True)
    
    bottom_container = st.container()
    with bottom_container:
        # ── Model selector + file uploader (same row) ─────────────
        col_model, col_spacer, col_upload = st.columns([5, 3, 2])

        with col_model:
            # Model selection with ^ button label
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
            'Wingman AI can make mistakes. Verify important information. See Cookie Preferences.'
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

    with st.spinner(""):
        ai_reply = ai_chat_response(
            prompt,
            model_choice=st.session_state.model,
            file_contexts=file_contexts,
        )

    save_chat(user_email, text, ai_reply, model=st.session_state.model, project_id=st.session_state.active_project_id)
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
