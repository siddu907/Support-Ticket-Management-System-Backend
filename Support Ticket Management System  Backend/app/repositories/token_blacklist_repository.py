from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.token_blacklist import TokenBlacklist


def is_token_blacklisted(db: Session, jti: str, token_type: str) -> bool:
    token = db.scalar(
        select(TokenBlacklist).where(
            TokenBlacklist.jti == jti,
            TokenBlacklist.token_type == token_type,
            TokenBlacklist.is_revoked.is_(True),
        )
    )
    if token is None:
        return False
    if token.expires_at.tzinfo is None:
        token.expires_at = token.expires_at.replace(tzinfo=timezone.utc)
    return token.expires_at > datetime.now(timezone.utc)


def blacklist_token(db: Session, user_id: int, jti: str, token_type: str, expires_at: datetime) -> None:
    if is_token_blacklisted(db, jti, token_type):
        return
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    db.add(TokenBlacklist(user_id=user_id, jti=jti, token_type=token_type, expires_at=expires_at, is_revoked=True))
