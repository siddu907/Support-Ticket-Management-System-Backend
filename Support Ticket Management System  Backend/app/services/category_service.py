from fastapi import HTTPException

from app.models.ticket_category import TicketCategory


def ensure_active(category: TicketCategory | None) -> TicketCategory:
	if category is None or not category.is_active:
		raise HTTPException(400, "Invalid or inactive category")
	return category
