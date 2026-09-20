from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserRoleUpdate, UserUpdate
from app.schemas.user import UserResponse
from app.repositories.user_repository import get_by_email, get_by_id, list_customer_tickets, list_users as repository_list_users
from app.services.user_service import activate, change_role as change_user_role, create as create_user_service, deactivate
from app.services.audit_service import record as record_audit

router = APIRouter()


def user_data(user: User) -> dict:
	return {"id": user.id, "name": user.name, "email": user.email, "role": user.role.name, "role_id": user.role_id, "is_active": user.is_active, "created_at": user.created_at.strftime("%Y-%m-%d %I:%M %p"), "updated_at": user.updated_at.strftime("%Y-%m-%d %I:%M %p")}


@router.post("", response_model=UserResponse, status_code=201)
def create_user(request: UserCreate, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	return user_data(create_user_service(db, request.name, str(request.email), request.password, request.role_id))


@router.get("", response_model=list[UserResponse])
def list_users(admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	return [user_data(user) for user in repository_list_users(db)]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	user = get_by_id(db, user_id)
	if user is None: raise HTTPException(404, "User not found")
	return user_data(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, request: UserUpdate, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	user = get_by_id(db, user_id)
	if user is None: raise HTTPException(404, "User not found")
	if request.email:
		existing = get_by_email(db, str(request.email))
		if existing and existing.id != user.id: raise HTTPException(409, "Email already exists")
	for field, value in request.model_dump(exclude_unset=True).items(): setattr(user, field, str(value).lower() if field == "email" else value)
	record_audit(db, admin.id, "USER_UPDATED", "User", user.id); db.commit(); db.refresh(user); return user_data(user)


@router.get("/{user_id}/tickets")
def user_tickets(user_id: int, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	if get_by_id(db, user_id) is None: raise HTTPException(404, "User not found")
	return list_customer_tickets(db, user_id)


def set_status(user_id: int, active: bool, db: Session):
	user = get_by_id(db, user_id)
	if user is None: raise HTTPException(404, "User not found")
	(activate if active else deactivate)(user); db.commit(); db.refresh(user); return user_data(user)


@router.put("/{user_id}/activate", response_model=UserResponse)
def activate_user(user_id: int, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)): return set_status(user_id, True, db)


@router.put("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(user_id: int, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)): return set_status(user_id, False, db)


@router.put("/{user_id}/role", response_model=UserResponse)
def change_role(user_id: int, request: UserRoleUpdate, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	user = get_by_id(db, user_id)
	if user is None: raise HTTPException(404, "User or role not found")
	return user_data(change_user_role(db, user, request.role_id))
