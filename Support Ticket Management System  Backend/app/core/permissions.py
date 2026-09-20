from fastapi import HTTPException

from app.models.user import User
from app.models.ticket import Ticket


def can_view_ticket(user: User, ticket: Ticket) -> bool:
	role = user.role.name
	return role == "Admin" or (role == "Customer" and ticket.customer_id == user.id) or (role == "Support Agent" and ticket.agent_id == user.id)


def ensure_ticket_access(user: User, ticket: Ticket) -> None:
	if not can_view_ticket(user, ticket):
		raise HTTPException(status_code=403, detail="You cannot access this ticket")
