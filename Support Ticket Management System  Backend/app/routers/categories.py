from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import TicketCategory, User
from app.schemas.ticket_category import TicketCategoryCreate, TicketCategoryResponse, TicketCategoryUpdate
from app.repositories.category_repository import get_by_id, get_by_name, list_all
from app.services.category_service import ensure_active

router = APIRouter()


@router.post("", response_model=TicketCategoryResponse, status_code=201)
def create_category(request: TicketCategoryCreate, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	if get_by_name(db, request.name): raise HTTPException(409, "Category already exists")
	category = TicketCategory(**request.model_dump()); db.add(category); db.commit(); db.refresh(category); return category


@router.get("", response_model=list[TicketCategoryResponse])
def list_categories(user: User = Depends(get_current_user), db: Session = Depends(get_db)): return list_all(db)


@router.get("/{category_id}", response_model=TicketCategoryResponse)
def get_category(category_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	category = get_by_id(db, category_id)
	if category is None: raise HTTPException(404, "Category not found")
	return category


@router.put("/{category_id}", response_model=TicketCategoryResponse)
def update_category(category_id: int, request: TicketCategoryUpdate, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	category = get_by_id(db, category_id)
	if category is None: raise HTTPException(404, "Category not found")
	for field, value in request.model_dump(exclude_unset=True).items(): setattr(category, field, value)
	db.commit(); db.refresh(category); return category


def set_status(category_id: int, active: bool, db: Session):
	category = get_by_id(db, category_id)
	if category is None: raise HTTPException(404, "Category not found")
	category.is_active = active; db.commit(); return category


@router.put("/{category_id}/activate", response_model=TicketCategoryResponse)
def activate_category(category_id: int, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)): return set_status(category_id, True, db)


@router.put("/{category_id}/deactivate", response_model=TicketCategoryResponse)
def deactivate_category(category_id: int, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)): return set_status(category_id, False, db)
