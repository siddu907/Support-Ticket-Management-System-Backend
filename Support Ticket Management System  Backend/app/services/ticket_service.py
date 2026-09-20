from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import PRIORITY_SLA_HOURS, STATUS_TRANSITIONS
from app.core.permissions import ensure_ticket_access
from app.models import Notification, Ticket, TicketCategory, TicketStatusHistory, User
from app.repositories.ticket_repository import build_list_query
from app.services.category_service import ensure_active
from app.services.notification_service import create as create_notification
from app.services.audit_service import record as record_audit


def notify_participants(db: Session, ticket: Ticket, notification_type: str, title: str, message: str, actor_id: int | None = None) -> None:
	for user_id in {ticket.customer_id, ticket.agent_id} - {None, actor_id}:
		create_notification(db, user_id, notification_type, title, message, ticket.id)


def create_ticket(db: Session, customer_id: int, title: str, description: str, category_id: int, priority: str, ip_address: str | None = None) -> Ticket:
	category = ensure_active(db.get(TicketCategory, category_id))
	if priority not in PRIORITY_SLA_HOURS:
		raise HTTPException(422, "Invalid priority")
	now = datetime.now(timezone.utc)
	ticket = Ticket(ticket_number=f"TKT-{uuid4().hex[:10].upper()}", title=title, description=description, customer_id=customer_id, category_id=category_id, priority=priority, due_date=now + timedelta(hours=PRIORITY_SLA_HOURS[priority]))
	db.add(ticket)
	db.flush()
	create_notification(db, customer_id, "TICKET_CREATED", "Ticket created", f"Ticket {ticket.ticket_number} was created", ticket.id)
	record_audit(db, customer_id, "TICKET_CREATED", "Ticket", ticket.id, {"priority": priority}, ip_address)
	db.commit()
	db.refresh(ticket)
	return ticket


def list_tickets(db: Session, user: User, **filters) -> tuple[list[Ticket], int]:
	page = max(filters.pop("page", 1), 1)
	page_size = min(max(filters.pop("page_size", 20), 1), 100)
	requested_customer = filters.pop("customer_id", None)
	requested_agent = filters.pop("assigned_agent_id", None)
	customer_id = user.id if user.role.name == "Customer" else requested_customer
	agent_id = user.id if user.role.name == "Support Agent" else requested_agent
	query = build_list_query(customer_id=customer_id, agent_id=agent_id, **filters)
	total = len(db.scalars(query.order_by(None)).all())
	items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
	return items, total


def change_status(db: Session, ticket: Ticket, user: User, new_status: str, ip_address: str | None = None) -> Ticket:
	ensure_ticket_access(user, ticket)
	new_status = {"open": "Open", "in progress": "In Progress", "resolved": "Resolved", "closed": "Closed"}.get(new_status.lower(), new_status)
	if user.role.name not in {"Admin", "Support Agent"}:
		raise HTTPException(403, "Only admins and agents can change ticket status")
	if new_status not in STATUS_TRANSITIONS.get(ticket.status, set()):
		raise HTTPException(400, f"Invalid status transition from {ticket.status} to {new_status}")
	old_status = ticket.status
	ticket.status = new_status
	db.add(TicketStatusHistory(ticket_id=ticket.id, changed_by=user.id, old_status=old_status, new_status=new_status))
	record_audit(db, user.id, "STATUS_CHANGED", "Ticket", ticket.id, {"old_status": old_status, "new_status": new_status}, ip_address)
	if new_status == "Closed": record_audit(db, user.id, "TICKET_CLOSED", "Ticket", ticket.id, None, ip_address)
	notify_participants(db, ticket, "TICKET_STATUS_CHANGED", "Ticket status changed", f"Ticket {ticket.ticket_number} changed from {old_status} to {new_status}", user.id)
	if new_status == "Resolved": notify_participants(db, ticket, "TICKET_RESOLVED", "Ticket resolved", f"Ticket {ticket.ticket_number} was resolved", user.id)
	if new_status == "Closed": notify_participants(db, ticket, "TICKET_CLOSED", "Ticket closed", f"Ticket {ticket.ticket_number} was closed", user.id)
	db.commit()
	db.refresh(ticket)
	return ticket


def update_ticket(db: Session, ticket: Ticket, user: User, values: dict, ip_address: str | None = None) -> Ticket:
	if ticket.status == "Closed":
		raise HTTPException(400, "Closed tickets cannot be modified")
	if "priority" in values:
		priority = values["priority"].title()
		if priority not in PRIORITY_SLA_HOURS: raise HTTPException(422, "Invalid priority")
		values["priority"] = priority
		ticket.due_date = ticket.created_at + timedelta(hours=PRIORITY_SLA_HOURS[priority])
	if "category_id" in values: values["category_id"] = ensure_active(db.get(TicketCategory, values["category_id"])).id
	for field, value in values.items(): setattr(ticket, field, value)
	record_audit(db, user.id, "TICKET_UPDATED", "Ticket", ticket.id, {"fields": list(values)}, ip_address)
	db.commit(); db.refresh(ticket); return ticket


def delete_ticket(db: Session, ticket: Ticket, user: User, ip_address: str | None = None) -> None:
	if user.role.name != "Admin": raise HTTPException(403, "Only admins can delete tickets")
	record_audit(db, user.id, "TICKET_DELETED", "Ticket", ticket.id, None, ip_address)
	db.delete(ticket); db.commit()


def assign_ticket(db: Session, ticket: Ticket, user: User, agent_id: int, reassign: bool, ip_address: str | None = None) -> Ticket:
	agent = db.scalar(select(User).options(joinedload(User.role)).where(User.id == agent_id))
	if user.role.name not in {"Admin", "Support Agent"}:
		raise HTTPException(403, "Only admins and agents can assign tickets")
	if user.role.name == "Support Agent" and (not reassign or ticket.agent_id != user.id):
		raise HTTPException(403, "Agents can only reassign their own tickets")
	if agent is None or agent.role.name != "Support Agent" or not agent.is_active:
		raise HTTPException(400, "Only active support agents can receive tickets")
	if reassign and ticket.agent_id is None:
		raise HTTPException(400, "Unassigned tickets must be assigned through the assign endpoint")
	if ticket.agent_id == agent.id:
		raise HTTPException(400, "This task is already assigned to this agent")
	if not reassign and ticket.agent_id is not None:
		raise HTTPException(400, "Assigned tickets must be reassigned through the reassign endpoint")
	previous_agent_id = ticket.agent_id
	ticket.agent_id = agent.id
	record_audit(db, user.id, "TICKET_REASSIGNED" if reassign else "TICKET_ASSIGNED", "Ticket", ticket.id, {"agent_id": agent.id}, ip_address)
	if reassign and previous_agent_id is not None and previous_agent_id != agent.id:
		create_notification(db, previous_agent_id, "TICKET_REASSIGNED", "Ticket reassigned", f"Ticket {ticket.ticket_number} was reassigned to another agent", ticket.id)
	notification_type = "TICKET_REASSIGNED" if reassign else "TICKET_ASSIGNED"
	notification_title = "Ticket reassigned" if reassign else "Ticket assigned"
	notification_message = f"Ticket {ticket.ticket_number} was reassigned to you" if reassign else f"Ticket {ticket.ticket_number} was assigned to you"
	create_notification(db, agent.id, notification_type, notification_title, notification_message, ticket.id)
	db.commit()
	db.refresh(ticket)
	return ticket
