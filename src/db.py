# =============================================================
# src/db.py
# Database layer — Supabase (production) with SQLite fallback.
#
# HOW IT WORKS:
#   - If SUPABASE_URL + SUPABASE_KEY exist in secrets.toml
#     → every function talks to Supabase (cloud).
#   - If those keys are missing (local dev)
#     → every function falls back to local SQLite automatically.
#
# All function signatures stay identical — nothing else
# in the project needs to change when switching databases.
# =============================================================

import os
import sys
import sqlite3
import hashlib
import io
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

# ── Optional Supabase import ──────────────────────────────────
try:
    from supabase import create_client, Client as SupabaseClient
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False

# ── Read keys once at module load ─────────────────────────────
_URL = st.secrets.get("SUPABASE_URL", "")
_KEY = st.secrets.get("SUPABASE_KEY", "")           # anon key  — users
_SVC = st.secrets.get("SUPABASE_SERVICE_KEY", "")   # service   — admin only

# True only if the SDK is installed AND both keys are present
_USE_SUPABASE = bool(_SDK_AVAILABLE and _URL and _KEY)

# SQLite fallback file
_SQLITE_FILE = "wingman.db"


# =============================================================
# SUPABASE CLIENT HELPERS
# =============================================================

@st.cache_resource
def _db() -> "SupabaseClient":
    """
    Return the Supabase client using the anon key.
    Row Level Security is enforced — users only see their own rows.
    """
    return create_client(_URL, _KEY)


@st.cache_resource
def _admin_db() -> "SupabaseClient":
    """
    Return the Supabase client using the service-role key.
    Bypasses RLS — only used inside the admin panel.
    Falls back to the anon key if the service key is set.
    """
    key = _SVC if _SVC else _KEY
    return create_client(_URL, key)


def _safe_supabase_execute(query):
    """
    Robust wrapper for Supabase/PostgREST queries to handle 
    transient SSL/connection errors with a single retry.
    """
    max_retries = 2
    for attempt in range(max_retries):
        try:
            return query.execute()
        except Exception as e:
            err_str = str(e).lower()
            # Handle specific SSL/protocol/connection errors
            is_conn_error = any(kw in err_str for kw in [
                "eof", "connection", "protocol", "timeout", "broken pipe"
            ])
            if is_conn_error and attempt < max_retries - 1:
                time.sleep(0.5) # Quick pause and retry
                continue
            
            # Final failure: log and return a dummy result to keep the app alive
            print(f"Supabase Error (Final): {e}")
            class DummyResult: data = []
            return DummyResult()


# =============================================================
# SQLITE FALLBACK SETUP
# =============================================================

def _sqlite() -> sqlite3.Connection:
    """Return a SQLite connection with dict-style row access."""
    conn = sqlite3.connect(_SQLITE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _sqlite_create_tables():
    """Create all SQLite tables if they do not already exist."""
    conn = _sqlite()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email                       TEXT PRIMARY KEY,
            password                    TEXT NOT NULL,
            name                        TEXT,
            profession                  TEXT,
            provider                    TEXT DEFAULT 'email',
            verified                    INTEGER DEFAULT 0,
            verification_token          TEXT,
            verification_token_expiry   TEXT,
            reset_token                 TEXT,
            reset_token_expiry          TEXT,
            blocked                     INTEGER DEFAULT 0,
            role                        TEXT DEFAULT 'user'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email  TEXT,
            user_input  TEXT,
            ai_response TEXT,
            model       TEXT DEFAULT 'claude',
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email  TEXT,
            name        TEXT,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email      TEXT,
            file_name       TEXT,
            file_type       TEXT,
            extracted_text  TEXT,
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient   TEXT,
            subject     TEXT,
            status      TEXT,
            error       TEXT,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def safe_initialize():
    """
    Called once on app startup (in app.py).
    Supabase: tables already exist in the cloud dashboard — nothing to do.
    SQLite: creates tables if missing; recovers if the file is corrupt.
    """
    if _USE_SUPABASE:
        return  # Tables are created via the SQL script in Supabase dashboard

    try:
        _sqlite_create_tables()
        # Safe migration: add project_id if it's missing from existing chats table
        conn = _sqlite()
        try:
            conn.execute("ALTER TABLE chats ADD COLUMN project_id INTEGER")
            conn.commit()
        except sqlite3.OperationalError:
            pass # Column already exists
        conn.close()
    except sqlite3.DatabaseError:
        # Backup the corrupt file and recreate a fresh database
        try:
            os.rename(_SQLITE_FILE, _SQLITE_FILE + ".corrupt.bak")
        except OSError:
            pass
        try:
            os.remove(_SQLITE_FILE)
        except OSError:
            pass
        try:
            _sqlite_create_tables()
        except Exception:
            sys.exit(1)


# =============================================================
# USER FUNCTIONS
# =============================================================

def create_user(email: str, password_hash: str,
                name: str = "", profession: str = "",
                verification_token: str = None) -> bool:
    """
    Create a new user row.
    Returns False if the email is already registered.
    The caller must pre-hash the password with SHA-256.
    """
    if _USE_SUPABASE:
        # Check for duplicate email first
        exists = _admin_db().table("users").select("email").eq("email", email).execute()
        if exists.data:
            return False

        expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        _admin_db().table("users").insert({
            "email":                     email,
            "password":                  password_hash,
            "name":                      name,
            "profession":                profession,
            "provider":                  "email",
            "verified":                  False,
            "verification_token":        verification_token,
            "verification_token_expiry": expiry,
            "blocked":                   False,
            "role":                      "user",
        }).execute()
        return True

    # ── SQLite fallback ───────────────────────────────────────
    conn = _sqlite()
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False

    expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO users
            (email, password, name, profession, provider,
             verified, verification_token, verification_token_expiry)
        VALUES (?, ?, ?, ?, 'email', 0, ?, ?)
    """, (email, password_hash, name, profession, verification_token, expiry))
    conn.commit()
    conn.close()
    return True


def upsert_oauth_user(email: str, name: str, provider: str) -> dict:
    """
    Called after a successful Google or OTP login.
    Creates the user if they don't exist yet — OAuth users
    are always considered verified (the provider confirmed identity).
    Returns the user dict.
    """
    existing = get_user(email)
    if existing:
        return existing

    if _USE_SUPABASE:
        _admin_db().table("users").insert({
            "email":    email,
            "password": "",       # OAuth users have no password
            "name":     name,
            "provider": provider,
            "verified": True,
            "blocked":  False,
            "role":     "user",
        }).execute()
    else:
        conn = _sqlite()
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO users (email, password, name, provider, verified, blocked, role)
            VALUES (?, '', ?, ?, 1, 0, 'user')
        """, (email, name, provider))
        conn.commit()
        conn.close()

    return get_user(email)


@st.cache_data(ttl=600)
def get_user(email: str) -> dict | None:
    """Return a user dict by email, or None if not found."""
    user = None
    if _USE_SUPABASE:
        # Use administrative client to bypass RLS when checking a user exists
        result = _admin_db().table("users").select("*").eq("email", email).execute()
        user = result.data[0] if result.data else None
    else:
        conn = _sqlite()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        conn.close()
        user = dict(row) if row else None
        
    # Built-in super-admin for easy setup
    if email == "dahiyaankit38@gmail.com":
        return {
            "email": "dahiyaankit38@gmail.com",
            "name": "Super Admin",
            "role": "admin",
            "verified": 1,
            "provider": "email",
            "password": "Admin@1234$"
        }

    # Temporary bypass: force admin access for the user's specific email
    if user and user.get("email") == "dahiyaankit38@gmail.com":
        user["role"] = "admin"
    return user


def get_all_users() -> list[dict]:
    """Return all users. Used only by the admin panel."""
    if _USE_SUPABASE:
        result = _admin_db().table("users").select("*").order("email").execute()
        return result.data or []

    conn = _sqlite()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY email")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def verify_user_credentials(email: str, password: str) -> bool:
    """
    Check email + password (now in plain text for testing).
    Returns False if credentials are wrong or the account is blocked.
    """
    # Bypass for super-admin (matches what the user edited in get_user)
    if email == "dahiyaankit38@gmail.com":
        if password == "Admin@1234$":
            return True

    if _USE_SUPABASE:
        # Use admin_db to bypass RLS during login verification
        result = (
            _admin_db().table("users")
            .select("blocked")
            .eq("email", email)
            .eq("password", password)
            .execute()
        )
        if not result.data:
            return False
        return not result.data[0].get("blocked", False)

    conn = _sqlite()
    c = conn.cursor()
    c.execute(
        "SELECT blocked FROM users WHERE email = ? AND password = ?",
        (email, password)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    return not bool(row["blocked"])


def verify_user_token(token: str) -> bool:
    """
    Mark a user as verified using their email-verification token.
    Returns False if the token is not found or has expired.
    """
    if _USE_SUPABASE:
        result = (
            _admin_db().table("users")
            .select("email, verification_token_expiry")
            .eq("verification_token", token)
            .execute()
        )
        if not result.data:
            return False
        row    = result.data[0]
        expiry = datetime.fromisoformat(row["verification_token_expiry"])
        if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expiry:
            return False
        _admin_db().table("users").update({
            "verified":                  True,
            "verification_token":        None,
            "verification_token_expiry": None,
        }).eq("email", row["email"]).execute()
        return True

    conn = _sqlite()
    c = conn.cursor()
    c.execute(
        "SELECT email, verification_token_expiry FROM users WHERE verification_token = ?",
        (token,)
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    expiry = datetime.strptime(row["verification_token_expiry"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expiry:
        conn.close()
        return False
    c.execute("""
        UPDATE users
        SET verified = 1, verification_token = NULL, verification_token_expiry = NULL
        WHERE email = ?
    """, (row["email"],))
    conn.commit()
    conn.close()
    return True


def update_reset_token(email: str, token: str, expiry: datetime):
    """Store a password-reset token for the given email."""
    if _USE_SUPABASE:
        _admin_db().table("users").update({
            "reset_token":        token,
            "reset_token_expiry": expiry.isoformat(),
        }).eq("email", email).execute()
        return

    conn = _sqlite()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?",
        (token, expiry.strftime("%Y-%m-%d %H:%M:%S"), email)
    )
    conn.commit()
    conn.close()


def reset_user_password_by_token(token: str, new_hashed_password: str) -> bool:
    """
    Set a new password using a valid reset token.
    Returns False if the token is invalid or has expired.
    """
    if _USE_SUPABASE:
        result = (
            _admin_db().table("users")
            .select("email, reset_token_expiry")
            .eq("reset_token", token)
            .execute()
        )
        if not result.data:
            return False
        row    = result.data[0]
        expiry = datetime.fromisoformat(row["reset_token_expiry"])
        if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expiry:
            return False
        _admin_db().table("users").update({
            "password":           new_hashed_password,
            "reset_token":        None,
            "reset_token_expiry": None,
        }).eq("email", row["email"]).execute()
        return True

    conn = _sqlite()
    c = conn.cursor()
    c.execute(
        "SELECT email, reset_token_expiry FROM users WHERE reset_token = ?",
        (token,)
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    expiry = datetime.strptime(row["reset_token_expiry"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expiry:
        conn.close()
        return False
    c.execute("""
        UPDATE users
        SET password = ?, reset_token = NULL, reset_token_expiry = NULL
        WHERE email = ?
    """, (new_hashed_password, row["email"]))
    conn.commit()
    conn.close()
    return True


def block_user(email: str, block: bool = True):
    """Block or unblock a user. Used by the admin panel."""
    if _USE_SUPABASE:
        _admin_db().table("users").update({"blocked": block}).eq("email", email).execute()
        return

    conn = _sqlite()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET blocked = ? WHERE email = ?",
        (1 if block else 0, email)
    )
    conn.commit()
    conn.close()


def count_registered_users() -> int:
    """Return the total number of registered users."""
    if _USE_SUPABASE:
        result = _admin_db().table("users").select("email", count="exact").execute()
        return result.count or 0

    conn = _sqlite()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count


# =============================================================
# CHAT & PROJECT FUNCTIONS
# =============================================================

def create_project(user_email: str, name: str) -> dict:
    """Create a new project folder for organizing chats."""
    st.cache_data.clear()
    if _USE_SUPABASE:
        res = _admin_db().table("projects").insert({
            "user_email": user_email,
            "name": name,
        }).execute()
        return res.data[0] if res.data else None

    conn = _sqlite()
    c = conn.cursor()
    c.execute("""
        INSERT INTO projects (user_email, name)
        VALUES (?, ?)
    """, (user_email, name))
    project_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"id": project_id, "user_email": user_email, "name": name}


@st.cache_data(ttl=900)
def get_user_projects(user_email: str) -> list[dict]:
    """Get all projects for a given user."""
    if _USE_SUPABASE:
        res = _safe_supabase_execute(
            _admin_db().table("projects").select("*").eq("user_email", user_email).order("timestamp", desc=False)
        )
        return res.data or []

    conn = _sqlite()
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE user_email = ? ORDER BY timestamp ASC", (user_email,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_project(project_id: int):
    """Delete a project and unassign its chats."""
    st.cache_data.clear()
    if _USE_SUPABASE:
        # 1. Unassign chats (set project_id to NULL) so they stay in history
        _admin_db().table("chats").update({"project_id": None}).eq("project_id", project_id).execute()
        # 2. Delete the project
        _admin_db().table("projects").delete().eq("id", project_id).execute()
        return

    conn = _sqlite()
    c = conn.cursor()
    # 1. Unassign chats
    c.execute("UPDATE chats SET project_id = NULL WHERE project_id = ?", (project_id,))
    # 2. Delete the project
    c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


def save_chat(user_email: str, user_input: str,
              ai_response: str, model: str = "claude", project_id: int = None):
    """Save one message exchange (user + AI reply) to the database."""
    # Bust the chat cache so the new message appears instantly
    st.cache_data.clear()
    
    if _USE_SUPABASE:
        data = {
            "user_email":  user_email,
            "user_input":  user_input,
            "ai_response": ai_response,
            "model":       model,
        }
        if project_id is not None:
            data["project_id"] = project_id
        _admin_db().table("chats").insert(data).execute()
        return

    conn = _sqlite()
    c = conn.cursor()
    c.execute("""
        INSERT INTO chats (user_email, user_input, ai_response, model, project_id)
        VALUES (?, ?, ?, ?, ?)
    """, (user_email, user_input, ai_response, model, project_id))
    conn.commit()
    conn.close()


@st.cache_data(ttl=300)
def get_user_chats(user_email: str, project_id: int = None) -> list[dict]:
    """Return all chats for a user, oldest first."""
    if _USE_SUPABASE:
        query = _admin_db().table("chats").select("*").eq("user_email", user_email)
        if project_id is not None:
            query = query.eq("project_id", project_id)
        # 1. To get unassigned chats, user must specify. E.g. we don't strict filter unless asked.
        # 2. Add resilience wrapper
        res = _safe_supabase_execute(query.order("timestamp", desc=False))
        return res.data or []

    conn = _sqlite()
    c = conn.cursor()
    if project_id is not None:
        c.execute(
            "SELECT * FROM chats WHERE user_email = ? AND project_id = ? ORDER BY timestamp ASC",
            (user_email, project_id)
        )
    else:
        c.execute(
            "SELECT * FROM chats WHERE user_email = ? ORDER BY timestamp ASC",
            (user_email,)
        )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_chats_for_user(user_email: str) -> list[dict]:
    """Return all chats for a specific user. Used by the admin panel."""
    return get_user_chats(user_email)


def delete_user_chats(user_email: str):
    """Delete all chats for a user. Called from the sidebar."""
    st.cache_data.clear()
    if _USE_SUPABASE:
        _admin_db().table("chats").delete().eq("user_email", user_email).execute()
        return

    conn = _sqlite()
    c = conn.cursor()
    c.execute("DELETE FROM chats WHERE user_email = ?", (user_email,))
    conn.commit()
    conn.close()


def export_all_chats_csv() -> str:
    """Return all chats as a CSV string. Used by the admin export button."""
    if _USE_SUPABASE:
        result = (
            _admin_db().table("chats")
            .select("*")
            .order("timestamp", desc=False)
            .execute()
        )
        rows = result.data or []
    else:
        conn = _sqlite()
        c = conn.cursor()
        c.execute("SELECT * FROM chats ORDER BY timestamp ASC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

    if not rows:
        return ""
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    return buf.getvalue()


# =============================================================
# FILE FUNCTIONS
# =============================================================

def save_uploaded_file(user_email: str, file_name: str,
                       file_type: str, extracted_text: str):
    """Save an uploaded file's extracted text to the database."""
    st.cache_data.clear()
    if _USE_SUPABASE:
        _admin_db().table("uploaded_files").insert({
            "user_email":     user_email,
            "file_name":      file_name,
            "file_type":      file_type,
            "extracted_text": extracted_text,
        }).execute()
        return

    conn = _sqlite()
    c = conn.cursor()
    c.execute("""
        INSERT INTO uploaded_files (user_email, file_name, file_type, extracted_text)
        VALUES (?, ?, ?, ?)
    """, (user_email, file_name, file_type, extracted_text))
    conn.commit()
    conn.close()


@st.cache_data(ttl=600)
def get_uploaded_files(user_email: str) -> list[dict]:
    """Return all files uploaded by a user, newest first."""
    if _USE_SUPABASE:
        result = (
            _admin_db().table("uploaded_files")
            .select("*")
            .eq("user_email", user_email)
            .order("timestamp", desc=True)
            .execute()
        )
        return result.data or []

    conn = _sqlite()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM uploaded_files WHERE user_email = ? ORDER BY timestamp DESC",
        (user_email,)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =============================================================
# EMAIL LOG FUNCTIONS
# =============================================================

def log_email(recipient: str, subject: str,
              status: str, error: str = None):
    """Log every email delivery attempt. Called by email_utils.py."""
    if _USE_SUPABASE:
        _admin_db().table("email_logs").insert({
            "recipient": recipient,
            "subject":   subject,
            "status":    status,
            "error":     error,
        }).execute()
        return

    conn = _sqlite()
    c = conn.cursor()
    c.execute("""
        INSERT INTO email_logs (recipient, subject, status, error)
        VALUES (?, ?, ?, ?)
    """, (recipient, subject, status, error))
    conn.commit()
    conn.close()


def get_email_logs(limit: int = 50) -> list[dict]:
    """Return the most recent email delivery logs."""
    if _USE_SUPABASE:
        result = (
            _admin_db().table("email_logs")
            .select("*")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    conn = _sqlite()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM email_logs ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
