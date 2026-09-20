from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
	return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
	return pwd_context.verify(password, hashed_password)


def create_token(subject: str, role: str, expires_delta: timedelta, token_type: str = "access") -> str:
	expires_at = datetime.now(timezone.utc) + expires_delta
	return jwt.encode({"sub": subject, "role": role, "type": token_type, "jti": str(uuid4()), "exp": expires_at}, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
	return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
