from fastapi import HTTPException

from app.models.ticket_comment import TicketComment
from app.models.user import User


def ensure_can_edit(comment: TicketComment, user: User) -> None:
	if comment.user_id != user.id and user.role.name != "Admin":
		raise HTTPException(403, "You can only modify your own comments")
