"""Add TR eligibility override table

Revision ID: bdb9cbb84083
Revises: 2301cbbba42c
Create Date: 2025-08-13 17:56:43.823727

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "bdb9cbb84083"
down_revision = "2301cbbba42c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create TR eligibility override table
    op.create_table(
        "tr_eligibility_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collaborator_id", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("is_eligible", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("modified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["modified_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_tr_eligibility_email"),
    )
    op.create_index(
        op.f("ix_tr_eligibility_overrides_collaborator_id"),
        "tr_eligibility_overrides",
        ["collaborator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tr_eligibility_overrides_email"),
        "tr_eligibility_overrides",
        ["email"],
        unique=False,
    )


def downgrade() -> None:
    # Drop TR eligibility override table
    op.drop_index(
        op.f("ix_tr_eligibility_overrides_email"), table_name="tr_eligibility_overrides"
    )
    op.drop_index(
        op.f("ix_tr_eligibility_overrides_collaborator_id"),
        table_name="tr_eligibility_overrides",
    )
    op.drop_table("tr_eligibility_overrides")
