import hashlib
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# pbkdf2_sha256 avoids the bcrypt backend compatibility issue present in newer
# bcrypt packages while still providing salted, adaptive password hashing.
# bcrypt remains listed for future verification of any legacy hashes.
_pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def validate_strong_password(password: str) -> str:
    if not any(char.islower() for char in password):
        raise ValueError("Password must include a lowercase letter")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must include an uppercase letter")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must include a number")
    return password


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, object] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Decode and validate a JWT access token.

    Returns the 'sub' claim on success, None if the token is invalid or expired.
    This function intentionally returns None rather than raising — it lives in
    core/ which has no dependency on exceptions/.  Callers in features/auth/
    are responsible for raising UnauthorizedError when None is returned.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        subject: str | None = payload.get("sub")
        return subject
    except JWTError:
        return None
