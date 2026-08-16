"""Add durable LLM classification audit decisions."""

import sqlalchemy as sa
from alembic import op

revision = "0002_classification_audit"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "classification_decisions" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "classification_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "message_id",
            sa.String(length=36),
            sa.ForeignKey("raw_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "model_version_id",
            sa.Integer(),
            sa.ForeignKey("model_versions.id"),
            nullable=False,
        ),
        sa.Column("is_weather_candidate", sa.Boolean(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("extraction_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "message_id", "model_version_id", name="uq_classification_message_model"
        ),
    )
    op.create_index(
        "ix_classification_decisions_message_id", "classification_decisions", ["message_id"]
    )
    op.create_index(
        "ix_classification_decisions_model_version_id",
        "classification_decisions",
        ["model_version_id"],
    )
    op.create_index(
        "ix_classification_decisions_accepted", "classification_decisions", ["accepted"]
    )
    op.create_index("ix_classification_decisions_reason", "classification_decisions", ["reason"])


def downgrade() -> None:
    if "classification_decisions" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("classification_decisions")
