# =============================================================
# src/admin.py
# Admin panel — only reachable by users with role = "admin".
# Routing is enforced in app.py before this function is called.
# =============================================================

import streamlit as st

from src.db import (
    get_all_users,
    get_all_chats_for_user,
    block_user,
    export_all_chats_csv,
    count_registered_users,
    get_email_logs,
)
from src.email_utils import _send_email


# =============================================================
# CSS — dark professional admin theme
# =============================================================

def _apply_admin_css():
    st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #0e0e16 !important;
    color: #e8e6f0 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
[data-testid="stSidebar"] > div:first-child {
    background: #0a0a14 !important;
    border-right: 1px solid #2e2e48 !important;
}
[data-testid="stSidebar"] * { color: #c8c6e8 !important; }

#MainMenu, footer, header,
[data-testid="stToolbar"],
.stDeployButton { display: none !important; }

.stButton > button {
    background: transparent !important;
    border: 1px solid #2e2e48 !important;
    color: #c8c6e8 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #1a1a2a !important;
    border-color: #534AB7 !important;
    color: #9F97E0 !important;
}
.stTextInput > div > div > input {
    background: #1a1a2a !important;
    border: 1px solid #2e2e48 !important;
    border-radius: 8px !important;
    color: #e8e6f0 !important;
}
.stMetric { background: #1a1a2a; border-radius: 8px; padding: 12px; }
hr { border-color: #2e2e48 !important; }

/* Admin dev bar at the top */
.admin-bar {
    background: #0a0a14;
    color: #6e6e8a;
    padding: 8px 16px;
    font-family: monospace;
    font-size: 11px;
    border-bottom: 1px solid #2e2e48;
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)


# =============================================================
# PUBLIC ENTRY POINT
# =============================================================

def show_admin_panel():
    """
    Render the admin panel.
    Called from app.py only when the logged-in user has role = "admin".
    """
    _apply_admin_css()

    admin_email = st.session_state.get("user", "admin")

    # Dev bar at the top
    from datetime import datetime
    st.markdown(
        f'<div class="admin-bar">'
        f'<span>⚙️  Wingman AI — Admin Panel</span>'
        f'<span>{admin_email} &nbsp;|&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.title("👑 Admin Dashboard")

    # Logout in sidebar
    with st.sidebar:
        st.markdown(f"**⚙️ Admin Panel**")
        st.caption(f"Logged in as **{admin_email}**")
        st.markdown("---")
        if st.button("🔒 End session", use_container_width=True):
            for key in ["user", "user_role"]:
                st.session_state[key] = None
            st.rerun()

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    all_users = get_all_users()
    active    = sum(1 for u in all_users if not u.get("blocked") and u.get("role") != "admin")
    blocked   = sum(1 for u in all_users if u.get("blocked"))

    col1.metric("Total users",    len(all_users))
    col2.metric("Active",         active)
    col3.metric("Blocked",        blocked)
    col4.metric("Admin access",   "✔ Active")

    st.markdown("---")

    # Tabs for the three main sections
    tab_users, tab_export, tab_email = st.tabs(
        ["👥 User Management", "📤 Export Data", "📧 Email Tools"]
    )

    with tab_users:
        _user_management_tab(all_users)

    with tab_export:
        _export_tab()

    with tab_email:
        _email_tab()


# =============================================================
# TAB — User Management
# =============================================================

def _user_management_tab(all_users: list[dict]):
    search = st.text_input("🔍 Search by name or email", key="admin_search")

    users = all_users
    if search:
        q = search.lower()
        users = [
            u for u in users
            if q in u["email"].lower() or q in u.get("name", "").lower()
        ]

    if not users:
        st.info("No users found.")
        return

    for i, user in enumerate(users):
        blocked  = bool(user.get("blocked"))
        is_admin = user.get("role") == "admin"

        col_info, col_status, col_block, col_chats = st.columns([3, 1, 1, 1])

        with col_info:
            st.markdown(
                f"**{user.get('name', 'Unnamed')}**  \n"
                f"📧 `{user['email']}`  \n"
                f"🧑‍💼 {user.get('profession', '—')} &nbsp;|&nbsp; "
                f"🛡️ `{user.get('role', 'user')}`"
            )

        with col_status:
            if is_admin:
                st.markdown("🟣 Admin")
            elif blocked:
                st.markdown("🔴 Blocked")
            else:
                st.markdown("🟢 Active")

        with col_block:
            if not is_admin:
                label = "🔓 Unblock" if blocked else "🔒 Block"
                if st.button(label, key=f"blk_{i}"):
                    block_user(user["email"], not blocked)
                    st.rerun()

        with col_chats:
            if st.button("💬 Chats", key=f"chats_{i}"):
                # Toggle the chat view for this user
                toggle_key = f"show_chats_{user['email']}"
                st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)
                st.rerun()

        # Expandable chat history below this user row
        if st.session_state.get(f"show_chats_{user['email']}", False):
            chats = get_all_chats_for_user(user["email"])
            if chats:
                with st.expander(
                    f"💬 {user['email']} — {len(chats)} messages",
                    expanded=True,
                ):
                    for chat in chats[-20:]:  # Show latest 20
                        ts = str(chat.get("timestamp", ""))[:16]
                        st.markdown(
                            f"**{ts}**  \n"
                            f"👤 {chat['user_input']}  \n"
                            f"🤖 {chat['ai_response']}"
                        )
                        st.markdown("---")
            else:
                st.info(f"No chat history for {user['email']}")

        st.markdown("---")


# =============================================================
# TAB — Export Data
# =============================================================

def _export_tab():
    st.subheader("Export all chat logs")
    st.caption("Downloads every message from every user as a single CSV file.")

    if st.button("📥 Generate CSV", key="gen_csv"):
        csv_data = export_all_chats_csv()
        if csv_data:
            st.download_button(
                label="📄 Download chat_history.csv",
                data=csv_data,
                file_name="chat_history.csv",
                mime="text/csv",
            )
        else:
            st.info("No chat data to export yet.")

    st.markdown("---")
    st.subheader("Email delivery logs")
    st.caption("Shows the last 50 emails sent by the app.")

    logs = get_email_logs(limit=50)
    if logs:
        import pandas as pd
        df = pd.DataFrame(logs)[["recipient", "subject", "status", "error", "timestamp"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No email logs yet.")


# =============================================================
# TAB — Email Tools
# =============================================================

def _email_tab():
    st.subheader("Send a test email")
    st.caption("Verify that your SMTP settings in secrets.toml are working.")

    recipient = st.text_input("Recipient email", placeholder="test@example.com")
    if st.button("✉️ Send test email", key="send_test_email"):
        if not recipient:
            st.warning("Please enter a recipient email.")
        else:
            ok = _send_email(
                recipient,
                "Test email from Wingman AI",
                "<p>This is a test email sent from the Wingman AI admin panel. "
                "Your SMTP configuration is working correctly.</p>",
            )
            if ok:
                st.success(f"✅ Test email sent to {recipient}")
            else:
                st.error("❌ Failed to send. Check EMAIL_* settings in secrets.toml.")
