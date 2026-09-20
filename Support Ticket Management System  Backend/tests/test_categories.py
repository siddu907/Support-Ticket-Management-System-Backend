from app.models.ticket_category import TicketCategory
from app.services.category_service import ensure_active


def test_active_category_is_accepted():
	category = TicketCategory(name="Technical", is_active=True)
	assert ensure_active(category) is category
