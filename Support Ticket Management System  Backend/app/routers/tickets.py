from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import PRIORITY_SLA_HOURS, STATUS_TRANSITIONS
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import ensure_ticket_access
from app.database import get_db
from app.models import Notification, Role, Ticket, TicketCategory, TicketStatusHistory, User
from app.repositories.ticket_repository import build_list_query, get_by_id
from app.schemas.ticket import TicketAssign, TicketCreate, TicketResponse, TicketStatusUpdate, TicketUpdate
from app.services.ticket_service import assign_ticket as service_assign_ticket, change_status as service_change_status, create_ticket as service_create_ticket, delete_ticket as service_delete_ticket, list_tickets as service_list_tickets, update_ticket as service_update_ticket
from app.services.audit_service import request_ip

router = APIRouter()


def parse_12h_datetime(value: str | None) -> datetime | None:
	if value in (None, ""):
		return None
	try:
		return datetime.fromisoformat(value.replace("Z", "+00:00"))
	except ValueError:
		pass
	for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %I:%M%p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%I:%M %p", "%Y-%m-%dT%H:%M:%S"):
		try:
			return datetime.strptime(value, fmt)
		except ValueError:
			continue
	raise HTTPException(400, f"Invalid datetime format: {value}. Use YYYY-MM-DD hh:mm AM/PM")


def ticket_data(ticket: Ticket) -> dict:
	format_time = lambda value: value.strftime("%Y-%m-%d %I:%M %p") if value else None
	return {"id": ticket.id, "ticket_number": ticket.ticket_number, "title": ticket.title, "description": ticket.description, "customer_id": ticket.customer_id, "agent_id": ticket.agent_id, "category_id": ticket.category_id, "priority": ticket.priority, "status": ticket.status, "due_date": format_time(ticket.due_date), "created_at": format_time(ticket.created_at), "updated_at": format_time(ticket.updated_at)}


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(request: TicketCreate, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	if user.role.name != "Customer":
		raise HTTPException(403, "Only customers can create tickets")
	return ticket_data(service_create_ticket(db, user.id, request.title, request.description, request.category_id, request.priority, request_ip(http_request)))


@router.get("")
def list_tickets(page: int = 1, page_size: int = 20, status: str | None = None, priority: str | None = None, category_id: int | None = None, assigned_agent_id: int | None = None, customer_id: int | None = None, search: str | None = None, date_from: str | None = None, date_to: str | None = None, sort_by: str = "created_at", sort_order: str = "desc", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	try:
		parsed_date_from = parse_12h_datetime(date_from)
		parsed_date_to = parse_12h_datetime(date_to)
		items, total = service_list_tickets(db, user, status=status.title() if status else None, priority=priority.title() if priority else None, category_id=category_id, assigned_agent_id=assigned_agent_id, customer_id=customer_id, search=search, date_from=parsed_date_from, date_to=parsed_date_to, sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size)
	except ValueError as error:
		raise HTTPException(400, str(error)) from error
	return {"total": total, "page": page, "page_size": page_size, "items": [ticket_data(item) for item in items]}


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	ensure_ticket_access(user, ticket)
	return ticket_data(ticket)


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: int, request: TicketUpdate, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	ensure_ticket_access(user, ticket)
	values = request.model_dump(exclude_unset=True)
	if "status" in values and values["status"] is not None:
		return ticket_data(service_change_status(db, ticket, user, values["status"], request_ip(http_request)))
	return ticket_data(service_update_ticket(db, ticket, user, values, request_ip(http_request)))


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	service_delete_ticket(db, ticket, user, request_ip(http_request))
	return {"message": "Ticket deleted"}


def assign_ticket(ticket_id: int, request: TicketAssign, http_request: Request, user: User, db: Session, reassign: bool):
	ticket = get_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	return ticket_data(service_assign_ticket(db, ticket, user, request.agent_id, reassign, request_ip(http_request)))


@router.put("/{ticket_id}/assign")
def assign(ticket_id: int, request: TicketAssign, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)): return assign_ticket(ticket_id, request, http_request, user, db, False)


@router.put("/{ticket_id}/reassign")
def reassign(ticket_id: int, request: TicketAssign, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)): return assign_ticket(ticket_id, request, http_request, user, db, True)


@router.put("/{ticket_id}/resolve")
def resolve_ticket(ticket_id: int, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	return ticket_data(service_change_status(db, ticket, user, "Resolved", request_ip(http_request)))


@router.put("/{ticket_id}/close")
def close_ticket(ticket_id: int, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	return ticket_data(service_change_status(db, ticket, user, "Closed", request_ip(http_request)))


@router.put("/{ticket_id}/reopen")
def reopen_ticket(ticket_id: int, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	return ticket_data(service_change_status(db, ticket, user, "Open", request_ip(http_request)))
