from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.database import get_db
from app.models import AuditLog, RefreshToken, Role, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, RefreshTokenRequest, RegisterRequest
from app.schemas.user import UserUpdate
from app.repositories.refresh_token_repository import get_active, revoke_user_tokens
from app.repositories.token_blacklist_repository import blacklist_token
from app.repositories.user_repository import get_by_email, get_by_id, get_role_by_name
from app.services.audit_service import record as record_audit, request_ip
from app.services.auth_service import authenticate, set_password

router = APIRouter()


def user_data(user: User) -> dict:
	return {"id": user.id, "name": user.name, "email": user.email, "role": user.role.name, "role_id": user.role_id, "is_active": user.is_active, "created_at": user.created_at.strftime("%Y-%m-%d %I:%M %p"), "updated_at": user.updated_at.strftime("%Y-%m-%d %I:%M %p")}


def token_pair(user: User, db: Session) -> dict:
	access = create_token(str(user.id), user.role.name, timedelta(minutes=settings.access_token_expire_minutes), "access")
	refresh = create_token(str(user.id), user.role.name, timedelta(days=settings.refresh_token_expire_days), "refresh")
	db.add(RefreshToken(user_id=user.id, token=refresh, expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)))
	db.commit()
	return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def login_response(user: User, db: Session) -> dict:
	payload = token_pair(user, db)
	payload["user"] = user_data(user)
	return payload


@router.post("/register", status_code=201)
def register(request: RegisterRequest, http_request: Request, db: Session = Depends(get_db)):
	if get_by_email(db, str(request.email)):
		raise HTTPException(409, "Email already exists")
	role = get_role_by_name(db, "Customer")
	if role is None:
		role = Role(name="Customer")
		db.add(role)
		db.flush()
	user = User(name=request.name, email=str(request.email).lower(), hashed_password=hash_password(request.password), role_id=role.id)
	db.add(user)
	db.flush()
	record_audit(db, user.id, "USER_CREATED", "User", user.id, {"source": "registration"}, request_ip(http_request))
	db.commit()
	db.refresh(user)
	return user_data(user)


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
	user = get_by_email(db, str(request.email))
	if not authenticate(user, request.password):
		record_audit(db, user.id if user else None, "FAILED_LOGIN", "User", user.id if user else None, {"email": str(request.email)}, request_ip(http_request))
		db.commit()
		raise HTTPException(401, "Invalid credentials")
	if not user.is_active:
		raise HTTPException(403, "Inactive users cannot authenticate")
	record_audit(db, user.id, "LOGIN", "User", user.id, {"authentication": "password"}, request_ip(http_request))
	db.commit()
	return login_response(user, db)


@router.get("/profile")
def profile(user: User = Depends(get_current_user)):
	return user_data(user)


@router.put("/change-password")
def change_password(request: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	if verify_password(request.new_password, user.hashed_password):
		raise HTTPException(400, "New password must be different from the current password")
	set_password(user, request.new_password)
	record_audit(db, user.id, "PASSWORD_CHANGED", "User", user.id)
	db.commit()
	return {"message": "Password changed successfully"}


@router.post("/refresh")
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
	try:
		payload = decode_token(request.refresh_token)
		user = get_by_id(db, int(payload["sub"]))
		stored = get_active(db, request.refresh_token)
	except (JWTError, KeyError, ValueError):
		user = None
		stored = None
	if user is None or stored is None or payload.get("type") != "refresh" or not user.is_active:
		raise HTTPException(401, "Invalid refresh token")
	stored.is_revoked = True
	return token_pair(user, db)


@router.post("/logout")
def logout(
	credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
	user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	payload = decode_token(credentials.credentials)
	jti = payload.get("jti")
	if jti:
		expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if payload.get("exp") is not None else datetime.now(timezone.utc) + timedelta(days=1)
		blacklist_token(db, user.id, jti, "access", expires_at)
	revoke_user_tokens(db, user.id)
	db.commit()
	return {"message": "Logged out successfully"}
