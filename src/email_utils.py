# =============================================================
# src/email_utils.py
# Email functions — verification and password-reset emails.
# All credentials come from st.secrets, never hardcoded.
# =============================================================

import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote

import streamlit as st

from src.db import log_email


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Internal helper — sends one HTML email via SMTP.
    Returns True on success, False on failure.
    Logs the result to the email_logs table either way.
    """
    host     = st.secrets.get("EMAIL_HOST")
    port     = int(st.secrets.get("EMAIL_PORT", 587))
    user     = st.secrets.get("EMAIL_USER")
    password = st.secrets.get("EMAIL_PASSWORD")

    # Fail early if credentials are missing
    if not all([host, user, password]):
        log_email(to_email, subject, "failed", "Missing SMTP credentials in secrets")
        return False

    try:
        msg = MIMEText(f"<html><body>{html_body}</body></html>", "html")
        msg["Subject"] = subject
        msg["From"]    = user
        msg["To"]      = to_email

        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_email], msg.as_string())
        server.quit()

        log_email(to_email, subject, "sent")
        return True

    except Exception as e:
        log_email(to_email, subject, "failed", str(e))
        return False


def send_verification_email(to_email: str, token: str) -> bool:
    """
    Send an account-verification email.
    The link includes the token so the user can verify with one click.
    """
    base_url = st.secrets.get("BASE_URL", "http://localhost:8501")
    link     = f"{base_url}/?verify_token={quote(token)}"

    subject = "Verify your Wingman AI account"
    body = f"""
        <h2>Welcome to Wingman AI 🤖</h2>
        <p>Click the button below to verify your email and activate your account.</p>
        <p>
          <a href="{link}"
             style="background:#19c37d;color:#fff;padding:12px 24px;
                    border-radius:8px;text-decoration:none;font-weight:600;">
            Verify my email
          </a>
        </p>
        <p style="color:#888;font-size:12px;">
          This link expires in 1 hour.<br>
          If you did not create an account, you can safely ignore this email.
        </p>
    """
    return _send_email(to_email, subject, body)


def send_reset_email(to_email: str, token: str) -> bool:
    """
    Send a password-reset email.
    The link includes the token so the user can set a new password.
    """
    base_url = st.secrets.get("BASE_URL", "http://localhost:8501")
    link     = f"{base_url}/?reset_token={quote(token)}"

    subject = "Reset your Wingman AI password"
    body = f"""
        <h2>Password Reset Request</h2>
        <p>Click the button below to set a new password for your account.</p>
        <p>
          <a href="{link}"
             style="background:#534AB7;color:#fff;padding:12px 24px;
                    border-radius:8px;text-decoration:none;font-weight:600;">
            Reset my password
          </a>
        </p>
        <p style="color:#888;font-size:12px;">
          This link expires in 1 hour.<br>
          If you did not request a password reset, you can safely ignore this email.
        </p>
    """
    return _send_email(to_email, subject, body)
