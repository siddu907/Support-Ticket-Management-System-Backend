import pytest
from fastapi import HTTPException

from app.models.role import Role
from app.models.ticket_comment import TicketComment
from app.models.user import User
from app.services.comment_service import ensure_can_edit


def test_comment_owner_can_edit():
	user = User(id=1, role=Role(name="Customer"))
	comment = TicketComment(user_id=1)
	ensure_can_edit(comment, user)


def test_comment_cannot_be_edited_by_another_user():
	comment = TicketComment(user_id=1)
	user = User(id=2, role=Role(name="Customer"))
	with pytest.raises(HTTPException) as error:
		ensure_can_edit(comment, user)
	assert error.value.status_code == 403
