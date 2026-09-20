from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ticket_category import TicketCategory
    from app.models.ticket_comment import TicketComment
    from app.models.ticket_attachment import TicketAttachment
    from app.models.ticket_status_history import TicketStatusHistory
    from app.models.notification import Notification

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticket_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("ticket_categories.id"), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Open", index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    customer: Mapped["User"] = relationship("User",foreign_keys=[customer_id],back_populates="customer_tickets")
    agent: Mapped["User | None"] = relationship("User",foreign_keys=[agent_id],back_populates="assigned_tickets")
    category: Mapped["TicketCategory"] = relationship("TicketCategory",back_populates="tickets")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="ticket", cascade="all, delete-orphan")
    comments: Mapped[list["TicketComment"]] = relationship("TicketComment",back_populates="ticket",cascade="all, delete-orphan")
    attachments: Mapped[list["TicketAttachment"]] = relationship("TicketAttachment",back_populates="ticket",cascade="all, delete-orphan")
    status_history: Mapped[list["TicketStatusHistory"]] = relationship("TicketStatusHistory",back_populates="ticket",cascade="all, delete-orphan")