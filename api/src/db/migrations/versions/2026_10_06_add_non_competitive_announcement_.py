"""add non-competitive announcement fields and application package recipients

Revision ID: 4b7e2c9d1a63
Revises: 058f456bcef7
Create Date: 2026-10-06 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4b7e2c9d1a63"
down_revision = "058f456bcef7"
branch_labels = None
depends_on = None


def _create_lookup_table(table_name: str, id_column: str) -> sa.Table:
    return op.create_table(
        table_name,
        sa.Column(id_column, sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(id_column, name=op.f(f"{table_name}_pkey")),
        schema="grantor",
    )


def upgrade():
    lk_announcement_type = _create_lookup_table("lk_announcement_type", "announcement_type_id")
    _create_lookup_table("lk_source_selection_method", "source_selection_method_id")
    _create_lookup_table("lk_performance_period_type", "performance_period_type_id")

    # Existing announcements get server default 1, so that row must exist before the FK is added.
    # The remaining lookup values are populated by the post-migration lookup sync.
    op.bulk_insert(
        lk_announcement_type, [{"announcement_type_id": 1, "description": "discretionary"}]
    )

    op.add_column(
        "announcement",
        sa.Column("announcement_type_id", sa.Integer(), server_default="1", nullable=False),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column(
            "is_budget_period_renewal", sa.Boolean(), server_default="false", nullable=False
        ),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("source_announcement_id", sa.UUID(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("original_announcement_number", sa.Text(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("source_selection_method_id", sa.Integer(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("cost_sharing_percentage", sa.Integer(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column(
            "allows_cash_contributions", sa.Boolean(), server_default="false", nullable=False
        ),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column(
            "allows_in_kind_contributions", sa.Boolean(), server_default="false", nullable=False
        ),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("performance_period_type_id", sa.Integer(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("performance_period_years", sa.Integer(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("budget_period_months", sa.Integer(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("agency_contact_name", sa.Text(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("agency_contact_phone", sa.Text(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("agency_email_address", sa.Text(), nullable=True),
        schema="grantor",
    )
    op.add_column(
        "announcement",
        sa.Column("agency_email_address_description", sa.Text(), nullable=True),
        schema="grantor",
    )
    op.create_index(
        op.f("announcement_announcement_type_id_idx"),
        "announcement",
        ["announcement_type_id"],
        unique=False,
        schema="grantor",
    )
    op.create_index(
        op.f("announcement_source_announcement_id_idx"),
        "announcement",
        ["source_announcement_id"],
        unique=False,
        schema="grantor",
    )
    op.create_foreign_key(
        op.f("announcement_announcement_type_id_lk_announcement_type_fkey"),
        "announcement",
        "lk_announcement_type",
        ["announcement_type_id"],
        ["announcement_type_id"],
        source_schema="grantor",
        referent_schema="grantor",
    )
    op.create_foreign_key(
        op.f("announcement_source_announcement_id_announcement_fkey"),
        "announcement",
        "announcement",
        ["source_announcement_id"],
        ["announcement_id"],
        source_schema="grantor",
        referent_schema="grantor",
    )
    op.create_foreign_key(
        op.f("announcement_source_selection_method_id_lk_source_selection_method_fkey"),
        "announcement",
        "lk_source_selection_method",
        ["source_selection_method_id"],
        ["source_selection_method_id"],
        source_schema="grantor",
        referent_schema="grantor",
    )
    op.create_foreign_key(
        op.f("announcement_performance_period_type_id_lk_performance_period_type_fkey"),
        "announcement",
        "lk_performance_period_type",
        ["performance_period_type_id"],
        ["performance_period_type_id"],
        source_schema="grantor",
        referent_schema="grantor",
    )

    op.create_table(
        "application_package_recipient",
        sa.Column("recipient_id", sa.UUID(), nullable=False),
        sa.Column("application_package_id", sa.UUID(), nullable=False),
        sa.Column("recipient_name", sa.Text(), nullable=False),
        sa.Column("recipient_type_id", sa.Integer(), nullable=False),
        sa.Column("email_address", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_package_id"],
            ["grantor.application_package.application_package_id"],
            name=op.f("application_package_recipient_application_package_id_application_package_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["recipient_type_id"],
            [
                "grantor.lk_application_package_open_to_applicant.application_package_open_to_applicant_id"
            ],
            name=op.f(
                "application_package_recipient_recipient_type_id_lk_application_package_open_to_applicant_fkey"
            ),
        ),
        sa.PrimaryKeyConstraint("recipient_id", name=op.f("application_package_recipient_pkey")),
        schema="grantor",
    )
    op.create_index(
        op.f("application_package_recipient_application_package_id_idx"),
        "application_package_recipient",
        ["application_package_id"],
        unique=False,
        schema="grantor",
    )


def downgrade():
    op.drop_index(
        op.f("application_package_recipient_application_package_id_idx"),
        table_name="application_package_recipient",
        schema="grantor",
    )
    op.drop_table("application_package_recipient", schema="grantor")

    op.drop_constraint(
        op.f("announcement_performance_period_type_id_lk_performance_period_type_fkey"),
        "announcement",
        schema="grantor",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("announcement_source_selection_method_id_lk_source_selection_method_fkey"),
        "announcement",
        schema="grantor",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("announcement_source_announcement_id_announcement_fkey"),
        "announcement",
        schema="grantor",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("announcement_announcement_type_id_lk_announcement_type_fkey"),
        "announcement",
        schema="grantor",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("announcement_source_announcement_id_idx"),
        table_name="announcement",
        schema="grantor",
    )
    op.drop_index(
        op.f("announcement_announcement_type_id_idx"),
        table_name="announcement",
        schema="grantor",
    )
    for column in (
        "agency_email_address_description",
        "agency_email_address",
        "agency_contact_phone",
        "agency_contact_name",
        "budget_period_months",
        "performance_period_years",
        "performance_period_type_id",
        "allows_in_kind_contributions",
        "allows_cash_contributions",
        "cost_sharing_percentage",
        "source_selection_method_id",
        "original_announcement_number",
        "source_announcement_id",
        "is_budget_period_renewal",
        "announcement_type_id",
    ):
        op.drop_column("announcement", column, schema="grantor")

    op.drop_table("lk_performance_period_type", schema="grantor")
    op.drop_table("lk_source_selection_method", schema="grantor")
    op.drop_table("lk_announcement_type", schema="grantor")
