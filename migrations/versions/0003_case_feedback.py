"""Store helpful / not-helpful ratings for retrieved incident precedents."""
from alembic import op
import sqlalchemy as sa

revision = "0003_case_feedback"
down_revision = "0002_incident_cases"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "case_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("investigation_id", sa.String(64), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_feedback_case_id", "case_feedback", ["case_id"])


def downgrade():
    op.drop_index("ix_case_feedback_case_id", table_name="case_feedback")
    op.drop_table("case_feedback")
