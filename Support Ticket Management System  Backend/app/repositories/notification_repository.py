from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


def list_for_user(db: Session, user_id: int) -> list[Notification]:
	return list(db.scalars(select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())).all())


def mark_all_read(db: Session, user_id: int) -> None:
	db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read.is_(False)).update({"is_read": True})


def get_for_user(db: Session, notification_id: int, user_id: int) -> Notification | None:
	return db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id))
