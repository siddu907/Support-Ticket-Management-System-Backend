from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import require_roles
from app.database import get_db
from app.models.user import User
from app.repositories.audit_repository import get_log, list_logs
from app.schemas.audit_log import AuditLogResponse

router = APIRouter()


@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	return list_logs(db)


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(log_id: int, admin: User = Depends(require_roles("Admin")), db: Session = Depends(get_db)):
	log = get_log(db, log_id)
	if log is None:
		raise HTTPException(404, "Audit log not found")
	return log
