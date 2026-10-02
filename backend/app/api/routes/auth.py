import os
import json
import time
import base64
import hmac
import hashlib
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from app.core.config import settings
from app.core.logging import logger
from app.database.supabase_client import in_memory_db, db_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

CREDENTIALS_FILE = os.path.join(settings.UPLOAD_DIR, "..", "admin_credentials.json")
CREDENTIALS_FILE = os.path.abspath(CREDENTIALS_FILE)

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@dhoodhplus.com"
DEFAULT_ADMIN_PASSWORD = getattr(settings, "ADMIN_PASSWORD", "admin123")

def _get_stored_credentials() -> Dict[str, str]:
    """Retrieve persisted admin credentials or fallback to defaults."""
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "email": data.get("email", DEFAULT_ADMIN_EMAIL),
                    "password": data.get("password", DEFAULT_ADMIN_PASSWORD)
                }
        except Exception as e:
            logger.warning(f"Failed to read credentials file: {e}")
    
    # Check in_memory_db or config
    email = in_memory_db.system_settings.get("admin_email", DEFAULT_ADMIN_EMAIL)
    password = in_memory_db.system_settings.get("admin_password", DEFAULT_ADMIN_PASSWORD)
    return {"email": email, "password": password}

def _save_credentials(email: str, password_hash: str):
    """Persist updated credentials to disk and database cache."""
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
    payload = {"email": email, "password": password_hash, "updated_at": time.time()}
    try:
        with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save credentials to file: {e}")

    in_memory_db.system_settings["admin_email"] = email
    in_memory_db.system_settings["admin_password"] = password_hash

    # Sync to Supabase if connected
    client = db_service.get_client()
    if db_service.is_connected and client:
        try:
            client.table("system_settings").update({
                "admin_email": email,
                "updated_at": "now()"
            }).eq("id", "default").execute()
        except Exception:
            pass

def hash_password(password: str) -> str:
    """Secure SHA-256 hash using application SECRET_KEY as salt."""
    salt = settings.SECRET_KEY.encode("utf-8")
    return hashlib.sha256(salt + password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, stored_credential: str) -> bool:
    """Verify against either plain text default or hashed credential."""
    if plain_password == stored_credential:
        return True
    return hash_password(plain_password) == stored_credential

def create_access_token(data: dict) -> str:
    """Create a signed HMAC-SHA256 access token with 30-day validity."""
    payload = dict(data)
    payload["exp"] = time.time() + (30 * 86400)
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    token = f"{base64.urlsafe_b64encode(payload_bytes).decode('utf-8')}.{sig}"
    return token

def verify_access_token(token: str) -> Optional[dict]:
    """Verify token signature and expiration."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_bytes = base64.urlsafe_b64decode(parts[0].encode("utf-8"))
        sig = parts[1]
        expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(payload_bytes.decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

# Request / Response Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class ChangeCredentialsRequest(BaseModel):
    current_password: str
    new_email: Optional[str] = None
    new_password: Optional[str] = None

@router.post("/login")
async def login(payload: LoginRequest):
    """
    Authenticate administrator with email or username and password.
    """
    creds = _get_stored_credentials()
    stored_email = creds["email"]
    stored_pass = creds["password"]

    username_input = payload.username.strip().lower()
    # Accept either registered email, 'admin', or the email username prefix
    stored_prefix = stored_email.split("@")[0].lower() if "@" in stored_email else "admin"
    email_matches = (
        username_input == stored_email.lower() or 
        username_input == "admin" or 
        username_input == stored_prefix
    )
    password_matches = verify_password(payload.password, stored_pass)

    if not (email_matches and password_matches):
        raise HTTPException(
            status_code=401,
            detail="Invalid email/username or password. Please try again."
        )

    token = create_access_token({
        "sub": stored_email,
        "role": "admin",
        "name": "Allah Ho Traders Admin"
    })

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": stored_email,
            "username": "admin",
            "name": "Allah Ho Traders Admin",
            "role": "admin"
        }
    }

@router.get("/profile")
async def get_profile(authorization: Optional[str] = Header(None)):
    """
    Get current admin profile and email.
    """
    creds = _get_stored_credentials()
    return {
        "email": creds["email"],
        "username": "admin",
        "name": "Allah Ho Traders Admin",
        "role": "admin",
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@router.post("/change-credentials")
async def change_credentials(payload: ChangeCredentialsRequest):
    """
    Update admin email address and/or password.
    Requires correct current password for security.
    """
    creds = _get_stored_credentials()
    stored_email = creds["email"]
    stored_pass = creds["password"]

    # 1. Validate current password
    if not verify_password(payload.current_password, stored_pass):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect. Please enter the correct current password."
        )

    updated_email = stored_email
    if payload.new_email and payload.new_email.strip():
        new_e = payload.new_email.strip().lower()
        if "@" not in new_e or "." not in new_e:
            raise HTTPException(status_code=400, detail="Please enter a valid email address.")
        updated_email = new_e

    updated_pass = stored_pass
    if payload.new_password and payload.new_password.strip():
        new_p = payload.new_password.strip()
        if len(new_p) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters long.")
        updated_pass = hash_password(new_p)

    # Persist
    _save_credentials(updated_email, updated_pass)

    return {
        "success": True,
        "message": "Credentials updated successfully! You can now log in with your new email and password.",
        "email": updated_email
    }
