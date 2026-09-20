from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.notification import Notification


def overdue_tickets(db: Session) -> list[Ticket]:
	now = datetime.now(timezone.utc)
	tickets = list(db.scalars(select(Ticket).where(Ticket.status.not_in(["Resolved", "Closed"]))).all())
	return [ticket for ticket in tickets if ticket.due_date and (ticket.due_date.replace(tzinfo=timezone.utc) if ticket.due_date.tzinfo is None else ticket.due_date) < now]


def create_sla_breach_notifications(db: Session) -> int:
	tickets = overdue_tickets(db)
	created = 0
	for ticket in tickets:
		if ticket.agent_id is None: continue
		exists = db.scalar(select(Notification).where(Notification.ticket_id == ticket.id, Notification.user_id == ticket.agent_id, Notification.notification_type == "SLA_BREACHED"))
		if exists is None:
			db.add(Notification(user_id=ticket.agent_id, ticket_id=ticket.id, notification_type="SLA_BREACHED", title="SLA breached", message=f"Ticket {ticket.ticket_number} is overdue"))
			created += 1
	db.commit()
	return created
