import os
import hashlib
import sys
from supabase import create_client

# Supabase Credentials (from environment variables or secrets.toml)
URL = os.environ.get("SUPABASE_URL", "")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "") # Use service key for admin creation

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin():
    try:
        client = create_client(URL, KEY)
        email = "admin@wingman.ai"
        password = "admin123"
        hashed = _hash_password(password)

        # Upsert the admin user directly into the public.users table
        # We bypass GoTrue auth for this bootstrap script since we manage 
        # our own sessions in st.session_state as seen in auth.py
        resp = client.table("users").upsert({
            "email": email,
            "password": hashed,
            "name": "Super Admin",
            "role": "admin",
            "verified": True,
            "provider": "email"
        }).execute()

        if resp.data:
            print(f"✅ Admin account successfully created/updated!")
            print(f"Email: {email}")
            print(f"Password: {password}")
        else:
            print(f"❌ Failed to create admin account: No data returned.")
    except Exception as e:
        print(f"❌ Error during admin creation: {e}")

if __name__ == "__main__":
    create_admin()
