from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_comment import TicketComment


def list_for_ticket(db: Session, ticket_id: int) -> list[TicketComment]:
	return list(db.scalars(select(TicketComment).where(TicketComment.ticket_id == ticket_id).order_by(TicketComment.created_at)).all())


def get_by_id(db: Session, comment_id: int) -> TicketComment | None:
	return db.get(TicketComment, comment_id)
