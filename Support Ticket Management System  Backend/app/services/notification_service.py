from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification import Notification


def create(db: Session, user_id: int, notification_type: str, title: str, message: str, ticket_id: int | None = None) -> Notification:
	notification = Notification(user_id=user_id, notification_type=notification_type, title=title, message=message, ticket_id=ticket_id)
	db.add(notification)
	return notification


def persist_background(user_id: int, notification_type: str, title: str, message: str, ticket_id: int | None = None) -> None:
	db = SessionLocal()
	try:
		create(db, user_id, notification_type, title, message, ticket_id)
		db.commit()
	finally:
		db.close()
