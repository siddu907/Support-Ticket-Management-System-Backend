from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
from app.repositories.user_repository import get_by_email, get_role
from app.core.security import hash_password
from fastapi import HTTPException


def activate(user: User) -> None:
	user.is_active = True


def deactivate(user: User) -> None:
	user.is_active = False


def delete(db: Session, user: User) -> None:
	user.is_active = False
	db.add(user)


def create(db: Session, name: str, email: str, password: str, role_id: int) -> User:
	if get_by_email(db, email):
		raise HTTPException(409, "Email already exists")
	role = get_role(db, role_id)
	if role is None:
		raise HTTPException(400, "Invalid role")
	user = User(name=name, email=email.lower(), hashed_password=hash_password(password), role_id=role.id)
	db.add(user)
	db.commit()
	db.refresh(user)
	return user


def change_role(db: Session, user: User, role_id: int) -> User:
	role = get_role(db, role_id)
	if role is None:
		raise HTTPException(404, "User or role not found")
	user.role_id = role.id
	db.commit()
	db.refresh(user)
	return user
