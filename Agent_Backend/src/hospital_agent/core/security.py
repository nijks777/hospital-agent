import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from hospital_agent.core.config import Settings

_password_hash = PasswordHash.recommended()  # Argon2id

# Verified when the username doesn't exist, so a wrong username takes as long as a wrong password.
# Otherwise response timing would reveal which usernames exist.
_DUMMY_HASH = _password_hash.hash("dummy-password-for-timing")

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    return _password_hash.verify(password, password_hash)


def create_access_token(user_id: uuid.UUID, role: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> dict[str, str]:
    """Raises jwt.InvalidTokenError if the token is invalid or expired."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_registration_token() -> str:
    return secrets.token_urlsafe(32)


def keyed_hash(value: str, settings: Settings) -> str:
    """HMAC-SHA256 with a server secret, for short-lived secrets (codes, registration tokens).

    A leaked DB row can't be brute-forced offline without the server key
    (a code has only 10^6 values).
    """
    return hmac.new(settings.jwt_secret_key.encode(), value.encode(), hashlib.sha256).hexdigest()


def keyed_hash_matches(value: str, expected_hash: str, settings: Settings) -> bool:
    return hmac.compare_digest(keyed_hash(value, settings), expected_hash)
