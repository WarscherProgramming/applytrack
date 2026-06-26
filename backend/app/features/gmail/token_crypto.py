"""Encryption for OAuth tokens at rest.

Isolated so the rest of the module never touches raw crypto. Tokens are
encrypted with Fernet (AES-128-CBC + HMAC) using a key derived from the app
SECRET_KEY — Gmail passwords are never involved or stored.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    # Fernet requires a 32-byte urlsafe-base64 key; derive it deterministically
    # from SECRET_KEY so the same deployment can always decrypt its own tokens.
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_token(plaintext: str | None) -> str | None:
    if not plaintext:
        return None
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str | None) -> str | None:
    if not ciphertext:
        return None
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # Wrong/rotated key — treat as no usable token rather than crashing.
        return None
