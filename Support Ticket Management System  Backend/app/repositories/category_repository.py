from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_category import TicketCategory


def get_by_id(db: Session, category_id: int) -> TicketCategory | None:
	return db.get(TicketCategory, category_id)


def list_active(db: Session) -> list[TicketCategory]:
	return list(db.scalars(select(TicketCategory).where(TicketCategory.is_active.is_(True)).order_by(TicketCategory.name)).all())


def list_all(db: Session) -> list[TicketCategory]:
	return list(db.scalars(select(TicketCategory).order_by(TicketCategory.name)).all())


def get_by_name(db: Session, name: str) -> TicketCategory | None:
	return db.scalar(select(TicketCategory).where(TicketCategory.name == name))
