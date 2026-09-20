from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
from uuid import uuid4
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user
from app.core.permissions import ensure_ticket_access
from app.database import get_db
from app.models import Ticket, TicketAttachment, User
from app.schemas.ticket_attachment import TicketAttachmentResponse
from app.services.attachment_service import read_upload
from app.repositories.attachment_repository import get_by_id, list_for_ticket
from app.repositories.ticket_repository import get_by_id as get_ticket_by_id
from app.services.audit_service import record as record_audit, request_ip

router = APIRouter()


@router.post("/tickets/{ticket_id}/attachments", response_model=TicketAttachmentResponse, status_code=201)
def upload_attachment(ticket_id: int, http_request: Request, file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_ticket_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	ensure_ticket_access(user, ticket)
	data = read_upload(file, settings.max_upload_size_bytes)
	path = Path(settings.upload_directory) / f"{uuid4().hex}_{Path(file.filename or 'attachment').name}"; path.write_bytes(data)
	attachment = TicketAttachment(ticket_id=ticket_id, uploader_id=user.id, file_name=file.filename or path.name, file_type=file.content_type or "application/octet-stream", file_size=len(data), file_path=str(path)); db.add(attachment); db.flush(); record_audit(db, user.id, "ATTACHMENT_UPLOADED", "TicketAttachment", attachment.id, {"file_type": file.content_type, "file_size": len(data)}, request_ip(http_request)); db.commit(); db.refresh(attachment); return attachment


@router.get("/tickets/{ticket_id}/attachments", response_model=list[TicketAttachmentResponse])
def list_attachments(ticket_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	ticket = get_ticket_by_id(db, ticket_id)
	if ticket is None: raise HTTPException(404, "Ticket not found")
	ensure_ticket_access(user, ticket); return list_for_ticket(db, ticket_id)


@router.get("/attachments/{attachment_id}")
def download_attachment(attachment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	attachment = get_by_id(db, attachment_id)
	if attachment is None: raise HTTPException(404, "Attachment not found")
	ensure_ticket_access(user, get_ticket_by_id(db, attachment.ticket_id)); return FileResponse(attachment.file_path, media_type=attachment.file_type, filename=attachment.file_name)


@router.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	attachment = get_by_id(db, attachment_id)
	if attachment is None: raise HTTPException(404, "Attachment not found")
	if attachment.uploader_id != user.id and user.role.name != "Admin": raise HTTPException(403, "You can only delete your own attachments")
	Path(attachment.file_path).unlink(missing_ok=True); db.delete(attachment); db.commit(); return {"message": "Attachment deleted"}
