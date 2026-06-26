"""Google OAuth 2.0 — isolated from the rest of the feature.

Only this module knows about Google's auth endpoints. The service depends on
these three functions and the TokenSet dataclass; nothing else imports them.
Uses httpx directly (already a dependency) so no Google SDK is required.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Read-only Gmail + the user's email address. We never request write scopes.
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]


@dataclass
class TokenSet:
    access_token: str
    refresh_token: str | None
    expires_at: datetime


class OAuthNotConfiguredError(RuntimeError):
    """Raised when a real OAuth call is attempted without credentials."""


def _require_config() -> None:
    if not settings.gmail_configured:
        raise OAuthNotConfiguredError(
            "Google OAuth is not configured (GOOGLE_CLIENT_ID/SECRET missing)."
        )


def build_authorization_url(state: str) -> str:
    """The URL to redirect the user to for consent."""
    _require_config()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        # offline + consent so Google returns a refresh token we can persist.
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _token_request(data: dict[str, str]) -> TokenSet:
    response = httpx.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    response.raise_for_status()
    payload = response.json()
    expires_in = int(payload.get("expires_in", 3600))
    return TokenSet(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token"),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    )


def exchange_code(code: str) -> TokenSet:
    """Exchange an authorization code for tokens."""
    _require_config()
    return _token_request(
        {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    )


def refresh_access_token(refresh_token: str) -> TokenSet:
    """Mint a fresh access token from a stored refresh token."""
    _require_config()
    tokens = _token_request(
        {
            "refresh_token": refresh_token,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }
    )
    # Refresh responses omit the refresh_token; keep the existing one.
    if tokens.refresh_token is None:
        tokens.refresh_token = refresh_token
    return tokens
