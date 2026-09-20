"""Add cascade delete for ticket child records.

Revision ID: 20260921_ticket_delete_cascade
Revises: 20260920_token_blacklist
Create Date: 2026-09-20

"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260921_ticket_delete_cascade"
down_revision: Union[str, Sequence[str], None] = "20260920_token_blacklist"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_ticket_id_fkey")
    op.execute("ALTER TABLE notifications ADD CONSTRAINT notifications_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE")

    op.execute("ALTER TABLE ticket_comments DROP CONSTRAINT IF EXISTS ticket_comments_ticket_id_fkey")
    op.execute("ALTER TABLE ticket_comments ADD CONSTRAINT ticket_comments_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE")

    op.execute("ALTER TABLE ticket_attachments DROP CONSTRAINT IF EXISTS ticket_attachments_ticket_id_fkey")
    op.execute("ALTER TABLE ticket_attachments ADD CONSTRAINT ticket_attachments_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE")

    op.execute("ALTER TABLE ticket_status_history DROP CONSTRAINT IF EXISTS ticket_status_history_ticket_id_fkey")
    op.execute("ALTER TABLE ticket_status_history ADD CONSTRAINT ticket_status_history_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE")


def downgrade() -> None:
    op.execute("ALTER TABLE ticket_status_history DROP CONSTRAINT IF EXISTS ticket_status_history_ticket_id_fkey")
    op.execute("ALTER TABLE ticket_status_history ADD CONSTRAINT ticket_status_history_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id)")

    op.execute("ALTER TABLE ticket_attachments DROP CONSTRAINT IF EXISTS ticket_attachments_ticket_id_fkey")
    op.execute("ALTER TABLE ticket_attachments ADD CONSTRAINT ticket_attachments_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id)")

    op.execute("ALTER TABLE ticket_comments DROP CONSTRAINT IF EXISTS ticket_comments_ticket_id_fkey")
    op.execute("ALTER TABLE ticket_comments ADD CONSTRAINT ticket_comments_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id)")

    op.execute("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_ticket_id_fkey")
    op.execute("ALTER TABLE notifications ADD CONSTRAINT notifications_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES tickets(id)")
