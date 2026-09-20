from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User
from app.repositories.token_blacklist_repository import is_token_blacklisted

security = HTTPBearer()


def get_current_user(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: Session = Depends(get_db),
) -> User:
	credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired credentials")
	try:
		payload = decode_token(credentials.credentials)
		if payload.get("type") != "access":
			raise ValueError("Invalid token type")
		user_id = int(payload.get("sub", ""))
		jti = payload.get("jti")
		if not jti or is_token_blacklisted(db, jti, "access"):
			raise ValueError("Token has been revoked")
	except (JWTError, ValueError, TypeError):
		raise credentials_error
	user = db.get(User, user_id)
	if user is None or not user.is_active:
		raise credentials_error
	return user


def require_roles(*roles: str):
	def dependency(user: User = Depends(get_current_user)) -> User:
		role = user.role.name if user.role else ""
		if role not in roles:
			raise HTTPException(status_code=403, detail="Insufficient permissions")
		return user
	return dependency
