from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def get_active(db: Session, token: str) -> RefreshToken | None:
	refresh_token = db.scalar(select(RefreshToken).where(RefreshToken.token == token, RefreshToken.is_revoked.is_(False)))
	if refresh_token is None:
		return None
	expires_at = refresh_token.expires_at
	if expires_at.tzinfo is None:
		expires_at = expires_at.replace(tzinfo=timezone.utc)
	if expires_at <= datetime.now(timezone.utc):
		return None
	return refresh_token


def revoke_user_tokens(db: Session, user_id: int) -> None:
	db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False)).update({"is_revoked": True})
