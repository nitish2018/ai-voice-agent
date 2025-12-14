"""
Security utilities for webhook verification and authentication.
"""
import hmac
import hashlib
from typing import Optional
from fastapi import HTTPException, Header, Request
from .config import settings


def verify_retell_signature(
    payload: bytes,
    signature: Optional[str],
    api_key: str
) -> bool:
    """
    Verify Retell AI webhook signature.
    
    Args:
        payload: Raw request body bytes
        signature: x-retell-signature header value
        api_key: Retell API key used for HMAC
        
    Returns:
        True if signature is valid
    """
    if not signature:
        return False
    
    expected_signature = hmac.new(
        api_key.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


async def verify_webhook_request(
    request: Request,
    x_retell_signature: Optional[str] = Header(None)
) -> bytes:
    """
    FastAPI dependency for verifying Retell webhook requests.
    
    Args:
        request: FastAPI request object
        x_retell_signature: Retell signature header
        
    Returns:
        Raw request body bytes
        
    Raises:
        HTTPException: If signature verification fails
    """
    body = await request.body()
    
    # In development mode, skip verification if no secret is set
    if settings.environment == "development" and not settings.retell_webhook_secret:
        return body
    
    if not verify_retell_signature(body, x_retell_signature, settings.retell_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )
    
    return body


# Authorized Retell server IPs for additional verification
RETELL_SERVER_IPS = ["13.248.202.14", "3.33.169.178"]


def verify_ip_address(client_ip: str) -> bool:
    """
    Verify request comes from authorized Retell server IP.
    
    Args:
        client_ip: Client IP address
        
    Returns:
        True if IP is authorized
    """
    return client_ip in RETELL_SERVER_IPS
