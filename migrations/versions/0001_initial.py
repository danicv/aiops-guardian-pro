"""Create the Guardian persistence schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("investigations",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("application", sa.String(128), nullable=False),
        sa.Column("environment", sa.String(32), nullable=False), sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False), sa.Column("root_cause", sa.Text()), sa.Column("confidence", sa.Float()),
        sa.Column("result", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("approvals",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("investigation_id", sa.String(64), nullable=False),
        sa.Column("action", sa.Text(), nullable=False), sa.Column("environment", sa.String(32), nullable=False),
        sa.Column("risk", sa.String(32), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("decided_by", sa.String(256)), sa.Column("comment", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)))
    op.create_index("ix_approvals_investigation_id", "approvals", ["investigation_id"])
    op.create_table("integrations",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False), sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("audit_events",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(256), nullable=False), sa.Column("entity_id", sa.String(128)),
        sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("conversations",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("application", sa.String(128), nullable=False),
        sa.Column("environment", sa.String(32), nullable=False), sa.Column("namespace", sa.String(128), nullable=False),
        sa.Column("telemetry_mode", sa.String(16), nullable=False), sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("messages", sa.JSON(), nullable=False), sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("conversations")
    op.drop_table("audit_events")
    op.drop_table("integrations")
    op.drop_index("ix_approvals_investigation_id", table_name="approvals")
    op.drop_table("approvals")
    op.drop_table("investigations")
