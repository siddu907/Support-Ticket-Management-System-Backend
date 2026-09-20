from sqlalchemy.orm import Session

from app.services.notification_service import persist_background


def queue_ticket_notification(db: Session, user_id: int, notification_type: str, title: str, message: str, ticket_id: int | None = None) -> None:
	persist_background(user_id, notification_type, title, message, ticket_id)
