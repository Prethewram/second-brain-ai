"""Add meeting minutes and links to notes/tasks.

Revision ID: a124c9d102ab
Revises: 160f32578b08
"""

from alembic import op
import sqlalchemy as sa

revision = "a124c9d102ab"
down_revision = "160f32578b08"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("meeting_date", sa.Date(), nullable=True),
        sa.Column("attendees", sa.Text(), nullable=False),
        sa.Column("agenda", sa.Text(), nullable=False),
        sa.Column("minutes", sa.Text(), nullable=False),
        sa.Column("decisions", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_meetings_id", "meetings", ["id"])
    op.create_index("ix_meetings_user_id", "meetings", ["user_id"])
    for table in ("notes", "tasks"):
        op.add_column(table, sa.Column("meeting_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_meeting_id",
            table,
            "meetings",
            ["meeting_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(f"ix_{table}_meeting_id", table, ["meeting_id"])


def downgrade():
    for table in ("tasks", "notes"):
        op.drop_index(f"ix_{table}_meeting_id", table_name=table)
        op.drop_constraint(f"fk_{table}_meeting_id", table, type_="foreignkey")
        op.drop_column(table, "meeting_id")
    op.drop_index("ix_meetings_user_id", table_name="meetings")
    op.drop_index("ix_meetings_id", table_name="meetings")
    op.drop_table("meetings")
