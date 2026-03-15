"""Initial schema - packages, analyses, alerts tables."""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "packages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("registry", sa.Enum("npm", "pypi", name="registrytype"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column("repository_url", sa.String(500), nullable=True),
        sa.Column("homepage_url", sa.String(500), nullable=True),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column(
            "threat_level",
            sa.Enum("safe", "low", "medium", "high", "critical", name="threatlevel"),
            nullable=True,
        ),
        sa.Column("is_malicious", sa.Boolean(), server_default="false"),
        sa.Column("weekly_downloads", sa.Integer(), server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("typosquatting_score", sa.Float(), server_default="0.0"),
        sa.Column("code_analysis_score", sa.Float(), server_default="0.0"),
        sa.Column("behavior_score", sa.Float(), server_default="0.0"),
        sa.Column("maintainer_score", sa.Float(), server_default="0.0"),
        sa.Column("dependency_score", sa.Float(), server_default="0.0"),
        sa.Column("typosquatting_evidence", sa.JSON(), nullable=True),
        sa.Column("code_patterns", sa.JSON(), nullable=True),
        sa.Column("behaviors", sa.JSON(), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=True),
        sa.Column("maintainer_flags", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "threat_level",
            sa.Enum("safe", "low", "medium", "high", "critical", name="threatlevel", create_type=False),
            nullable=True,
        ),
        sa.Column("is_read", sa.Boolean(), server_default="false"),
        sa.Column("is_resolved", sa.Boolean(), server_default="false"),
        sa.Column("registry_reported", sa.Boolean(), server_default="false"),
        sa.Column("blocked_in_ci", sa.Boolean(), server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("analyses")
    op.drop_table("packages")
    op.execute("DROP TYPE IF EXISTS threatlevel")
    op.execute("DROP TYPE IF EXISTS registrytype")
