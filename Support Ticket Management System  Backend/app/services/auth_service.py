from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.security import create_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import get_by_email


def authenticate(user: User | None, password: str) -> bool:
	return user is not None and user.is_active and verify_password(password, user.hashed_password)


def find_user_by_email(db: Session, email: str) -> User | None:
	return get_by_email(db, email)


def create_access_token(user: User, minutes: int) -> str:
	return create_token(str(user.id), user.role.name, timedelta(minutes=minutes), "access")


def set_password(user: User, password: str) -> None:
	user.hashed_password = hash_password(password)
