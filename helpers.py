from __future__ import annotations

import time
import uuid
from typing import Optional

from api_client import StellarApiClient


def unique_email(domain: str = "example.com") -> str:
    """Generate a unique email for test users.

    Example: user_ab12cd34ef56@example.com
    """
    return f"user_{uuid.uuid4().hex[:12]}@{domain}"


def _extract_token_from_login(client: StellarApiClient, email: str, password: str) -> Optional[str]:
    try:
        res = client.auth_login(email, password)
        if res.status_code == 200 and res.json and res.json.get("accessToken"):
            return res.json.get("accessToken", "").replace("Bearer ", "")
    except Exception:
        pass
    return None


def delete_user_safely(client: StellarApiClient, email: str, password: str, token: Optional[str] = None, attempts: int = 3, delay: float = 0.5) -> bool:
    """Attempt to delete a user reliably.

    - Tries with provided token (if any)
    - Falls back to logging in for a fresh token
    - Retries a few times with a short backoff
    Returns True if deletion appears successful.
    """
    for _ in range(max(1, attempts)):
        # Try with the token we have
        if token:
            try:
                res = client.auth_user_delete(token)
                if res.status_code in (200, 202) and res.json and res.json.get("success") is True:
                    return True
            except Exception:
                pass
        # Fallback: login to obtain a fresh token, then delete
        fresh_token = _extract_token_from_login(client, email, password)
        if fresh_token:
            try:
                res = client.auth_user_delete(fresh_token)
                if res.status_code in (200, 202) and res.json and res.json.get("success") is True:
                    return True
            except Exception:
                pass
        time.sleep(delay)
    return False
