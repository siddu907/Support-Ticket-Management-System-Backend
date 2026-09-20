from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


def ticket_counts(db: Session, agent_id: int | None = None) -> dict[str, int]:
	query = select(Ticket)
	if agent_id is not None: query = query.where(Ticket.agent_id == agent_id)
	tickets = db.scalars(query).all()
	now = datetime.now(timezone.utc)
	overdue = sum(bool(t.due_date and (t.due_date.replace(tzinfo=timezone.utc) if t.due_date.tzinfo is None else t.due_date) < now and t.status not in {"Resolved", "Closed"}) for t in tickets)
	result = {"total_tickets": len(tickets), "open_tickets": sum(t.status == "Open" for t in tickets), "in_progress_tickets": sum(t.status == "In Progress" for t in tickets), "resolved_tickets": sum(t.status == "Resolved" for t in tickets), "closed_tickets": sum(t.status == "Closed" for t in tickets), "overdue_tickets": overdue, "critical_tickets": sum(t.priority == "Critical" for t in tickets)}
	if agent_id is not None:
		result.update({"my_open_tickets": sum(t.status in {"Open", "In Progress"} for t in tickets), "my_overdue_tickets": overdue, "my_resolved_tickets": sum(t.status == "Resolved" for t in tickets)})
	return result


def admin_counts(db: Session) -> dict:
	from app.models.user import User
	tickets = db.scalars(select(Ticket)).all()
	users = db.scalars(select(User)).all()
	result = ticket_counts(db)
	result.update({"total_customers": sum(user.role.name == "Customer" for user in users), "total_agents": sum(user.role.name == "Support Agent" for user in users), "active_agents": sum(user.role.name == "Support Agent" and user.is_active for user in users), "tickets_per_agent": {str(user.id): len(user.assigned_tickets) for user in users if user.role.name == "Support Agent"}})
	return result
