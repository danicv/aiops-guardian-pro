"""Add searchable synthetic and historical incident cases."""
from alembic import op
import sqlalchemy as sa

revision = "0002_incident_cases"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "incident_cases",
        sa.Column("case_id", sa.String(64), primary_key=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("service", sa.String(128), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("symptoms", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("remediation", sa.JSON(), nullable=False),
        sa.Column("verification", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incident_cases_category", "incident_cases", ["category"])
    op.create_index("ix_incident_cases_service", "incident_cases", ["service"])


def downgrade():
    op.drop_index("ix_incident_cases_service", table_name="incident_cases")
    op.drop_index("ix_incident_cases_category", table_name="incident_cases")
    op.drop_table("incident_cases")
