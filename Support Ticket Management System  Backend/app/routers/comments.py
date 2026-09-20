from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.permissions import ensure_ticket_access
from app.database import get_db
from app.models import Ticket, TicketComment, User
from app.schemas.ticket_comment import TicketCommentCreate, TicketCommentResponse, TicketCommentUpdate
from app.repositories.comment_repository import get_by_id, list_for_ticket
from app.repositories.ticket_repository import get_by_id as get_ticket_by_id
from app.services.comment_service import ensure_can_edit
from app.services.audit_service import record as record_audit, request_ip
from app.services.notification_service import persist_background

router = APIRouter()


@router.post("/tickets/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=201)
def add_comment(ticket_id: int, request: TicketCommentCreate, background_tasks: BackgroundTasks, http_request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_ticket_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	ensure_ticket_access(user, ticket)
	if ticket.status == "Closed": raise HTTPException(400, "Closed tickets cannot receive comments")
	comment = TicketComment(ticket_id=ticket_id, user_id=user.id, content=request.content); db.add(comment); db.flush(); record_audit(db, user.id, "COMMENT_ADDED", "TicketComment", comment.id, {"ticket_id": ticket.id}, request_ip(http_request))
	db.commit(); db.refresh(comment)
	for recipient_id in {ticket.customer_id, ticket.agent_id} - {None, user.id}: background_tasks.add_task(persist_background, recipient_id, "NEW_COMMENT", "New ticket comment", f"A new comment was added to {ticket.ticket_number}", ticket.id)
	return comment


@router.get("/tickets/{ticket_id}/comments", response_model=list[TicketCommentResponse])
def list_comments(ticket_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_ticket_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	ensure_ticket_access(user, ticket)
	return list_for_ticket(db, ticket_id)


@router.put("/comments/{comment_id}", response_model=TicketCommentResponse)
def update_comment(comment_id: int, request: TicketCommentUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	comment = get_by_id(db, comment_id)
	if comment is None: raise HTTPException(404, "Comment not found")
	ensure_can_edit(comment, user)
	comment.content = request.content; db.commit(); db.refresh(comment); return comment


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	comment = get_by_id(db, comment_id)
	if comment is None: raise HTTPException(404, "Comment not found")
	ensure_can_edit(comment, user)
	db.delete(comment); db.commit(); return {"message": "Comment deleted"}
