from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import Notification, User
from app.repositories.notification_repository import get_for_user, list_for_user, mark_all_read
from app.schemas.notification import NotificationResponse

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
def notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return list_for_user(db, user.id)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def read_notification(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	notification = get_for_user(db, notification_id, user.id)
	if notification is None: raise HTTPException(404, "Notification not found")
	notification.is_read = True; db.commit(); return notification


@router.put("/read-all")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	mark_all_read(db, user.id); db.commit(); return {"message": "Notifications marked as read"}
