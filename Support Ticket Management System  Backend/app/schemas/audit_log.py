from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer

class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    ip_address: str | None
    log_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %I:%M %p")