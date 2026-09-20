from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket

SORTABLE_FIELDS = {"created_at", "updated_at", "priority", "status", "due_date"}


def get_by_id(db: Session, ticket_id: int) -> Ticket | None:
	return db.get(Ticket, ticket_id)


def build_list_query(customer_id: int | None = None, agent_id: int | None = None, status: str | None = None, priority: str | None = None, category_id: int | None = None, search: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None, sort_by: str = "created_at", sort_order: str = "desc") -> Select:
	query = select(Ticket)
	if customer_id is not None: query = query.where(Ticket.customer_id == customer_id)
	if agent_id is not None: query = query.where(Ticket.agent_id == agent_id)
	if status is not None: query = query.where(Ticket.status == status)
	if priority is not None: query = query.where(Ticket.priority == priority)
	if category_id is not None: query = query.where(Ticket.category_id == category_id)
	if search: query = query.where(Ticket.title.ilike(f"%{search}%") | Ticket.description.ilike(f"%{search}%"))
	if date_from is not None: query = query.where(Ticket.created_at >= date_from)
	if date_to is not None: query = query.where(Ticket.created_at <= date_to)
	if sort_by not in SORTABLE_FIELDS:
		raise ValueError(f"Unsupported ticket sort field: {sort_by}")
	if sort_order.lower() not in {"asc", "desc"}:
		raise ValueError(f"Unsupported ticket sort order: {sort_order}")
	column = getattr(Ticket, sort_by)
	query = query.order_by(column.asc() if sort_order.lower() == "asc" else column.desc())
	return query
