from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def list_logs(db: Session) -> list[AuditLog]:
	return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc())).all())


def get_log(db: Session, log_id: int) -> AuditLog | None:
	return db.get(AuditLog, log_id)
