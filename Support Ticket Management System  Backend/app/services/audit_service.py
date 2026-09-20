from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record(db: Session, user_id: int | None, action: str, entity_type: str, entity_id: int | None = None, metadata: dict | None = None, ip_address: str | None = None) -> AuditLog:
	entry = AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, log_metadata=metadata, ip_address=ip_address)
	db.add(entry)
	return entry


def request_ip(request) -> str | None:
	return request.client.host if request.client else None
