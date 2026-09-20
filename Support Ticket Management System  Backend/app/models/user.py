from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.ticket import Ticket
    from app.models.ticket_comment import TicketComment
    from app.models.ticket_attachment import TicketAttachment
    from app.models.notification import Notification
    from app.models.audit_log import AuditLog
    from app.models.refresh_token import RefreshToken

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    role: Mapped["Role"] = relationship("Role",back_populates="users")
    customer_tickets: Mapped[list["Ticket"]] = relationship("Ticket",foreign_keys="Ticket.customer_id",back_populates="customer")
    assigned_tickets: Mapped[list["Ticket"]] = relationship("Ticket",foreign_keys="Ticket.agent_id",back_populates="agent")
    comments: Mapped[list["TicketComment"]] = relationship("TicketComment",back_populates="user")
    attachments: Mapped[list["TicketAttachment"]] = relationship("TicketAttachment",back_populates="uploader")
    notifications: Mapped[list["Notification"]] = relationship("Notification",back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog",back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken",back_populates="user")