from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Role, Ticket, User


def get_by_id(db: Session, user_id: int) -> User | None:
	return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))


def get_by_email(db: Session, email: str) -> User | None:
	return db.scalar(select(User).options(joinedload(User.role)).where(User.email == email.lower()))


def list_users(db: Session) -> list[User]:
	return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def get_role(db: Session, role_id: int) -> Role | None:
	return db.get(Role, role_id)


def get_role_by_name(db: Session, name: str) -> Role | None:
	return db.scalar(select(Role).where(Role.name == name))


def list_customer_tickets(db: Session, user_id: int) -> list[Ticket]:
	return list(db.scalars(select(Ticket).where(Ticket.customer_id == user_id).order_by(Ticket.created_at.desc())).all())
