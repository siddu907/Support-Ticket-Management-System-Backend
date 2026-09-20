from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_attachment import TicketAttachment
from app.repositories.ticket_repository import get_by_id as get_ticket_by_id


def list_for_ticket(db: Session, ticket_id: int) -> list[TicketAttachment]:
	return list(db.scalars(select(TicketAttachment).where(TicketAttachment.ticket_id == ticket_id)).all())


def get_by_id(db: Session, attachment_id: int) -> TicketAttachment | None:
	return db.get(TicketAttachment, attachment_id)
