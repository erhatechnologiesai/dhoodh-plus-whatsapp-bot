import hmac
import hashlib
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security_scheme = HTTPBearer(auto_error=False)

def verify_admin_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)) -> bool:
    """
    Validates admin bearer token or development bypass.
    """
    if settings.ENV == "development" and not credentials:
        # In development mode, allow easy testing if no token provided
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication credentials missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check bearer token against SECRET_KEY or ADMIN_PASSWORD
    token = credentials.credentials
    if token != settings.SECRET_KEY and token != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials",
        )
    return True

def verify_whatsapp_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """
    Verifies that the incoming webhook payload was signed by Meta WhatsApp Cloud API.
    Header format: sha256=<hash>
    """
    if not settings.WHATSAPP_APP_SECRET:
        # If app secret not configured, skip HMAC check (e.g. testing)
        return True
        
    if not signature_header or not signature_header.startswith("sha256="):
        return False
        
    expected_hash = signature_header[7:]
    mac = hmac.new(
        key=settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    )
    return hmac.compare_digest(mac.hexdigest(), expected_hash)
