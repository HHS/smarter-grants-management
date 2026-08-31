"""add grantor org triggers

Revision ID: 9998d48622ed
Revises: 438ae6a69f76
Create Date: 2026-08-31 14:20:20.628548

"""

import sqlalchemy as sa
from alembic import op

from src.db.migrations.db_functions import (
    get_grantor_organization_insert_automation_sql,
    get_grantor_organization_update_automation_sql,
)

# revision identifiers, used by Alembic.
revision = "9998d48622ed"
down_revision = "438ae6a69f76"
branch_labels = None
depends_on = None


def upgrade():
    # Create DB triggers for auto-populating the paths
    op.execute(sa.text(get_grantor_organization_insert_automation_sql("grantor")))
    op.execute(sa.text(get_grantor_organization_update_automation_sql("grantor")))


def downgrade():
    # If we were to downgrade this, we'd leave the triggers/functions
    # as we'd just fix them if there were an issue.
    pass
