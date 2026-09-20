from app.models.user import User
from app.services.user_service import activate, deactivate


def test_user_activation_service_changes_status():
	user = User(is_active=True)
	deactivate(user)
	assert user.is_active is False
	activate(user)
	assert user.is_active is True


def test_audit_response_serializes_datetime_in_12_hour_format():
	from datetime import datetime

	from app.models.audit_log import AuditLog
	from app.schemas.audit_log import AuditLogResponse

	audit = AuditLog(id=1, action="LOGIN", entity_type="User", created_at=datetime(2026, 9, 20, 13, 5))
	response = AuditLogResponse.model_validate(audit)

	assert response.model_dump(mode="json")["created_at"] == "2026-09-20 01:05 PM"
