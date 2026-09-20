from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_roles
from app.database import get_db
from app.models import Ticket, User
from app.services.dashboard_service import admin_counts, ticket_counts

router = APIRouter()


def counts(tickets: list[Ticket]) -> dict:
	now = datetime.now(timezone.utc)
	overdue = sum(bool(ticket.due_date and (ticket.due_date.replace(tzinfo=timezone.utc) if ticket.due_date.tzinfo is None else ticket.due_date) < now and ticket.status not in {"Resolved", "Closed"}) for ticket in tickets)
	return {"total_tickets": len(tickets), "open_tickets": sum(ticket.status == "Open" for ticket in tickets), "in_progress_tickets": sum(ticket.status == "In Progress" for ticket in tickets), "resolved_tickets": sum(ticket.status == "Resolved" for ticket in tickets), "closed_tickets": sum(ticket.status == "Closed" for ticket in tickets), "overdue_tickets": overdue, "critical_tickets": sum(ticket.priority == "Critical" for ticket in tickets)}


@router.get("/admin")
def admin_dashboard(admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	return admin_counts(db)


@router.get("/support-agent")
def agent_dashboard(agent: User = Depends(require_roles("Support Agent")), db: Session = Depends(get_db)):
	return ticket_counts(db, agent.id)
