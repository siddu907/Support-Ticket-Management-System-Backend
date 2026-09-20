"""Add operational indexes for ticket filtering and audit queries."""

from alembic import op
import sqlalchemy as sa

revision = "20260919_indexes"
down_revision = "633715651e9c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, name)
            VALUES (1, 'Admin'), (2, 'Customer'), (3, 'Support Agent')
            ON CONFLICT (name) DO UPDATE SET id = EXCLUDED.id
            """
        )
    )
    op.create_index("ix_tickets_status_priority", "tickets", ["status", "priority"], unique=False)
    op.create_index("ix_tickets_customer_created", "tickets", ["customer_id", "created_at"], unique=False)
    op.create_index("ix_tickets_agent_created", "tickets", ["agent_id", "created_at"], unique=False)


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name IN ('Admin', 'Support Agent', 'Customer')")
    op.drop_index("ix_tickets_agent_created", table_name="tickets")
    op.drop_index("ix_tickets_customer_created", table_name="tickets")
    op.drop_index("ix_tickets_status_priority", table_name="tickets")