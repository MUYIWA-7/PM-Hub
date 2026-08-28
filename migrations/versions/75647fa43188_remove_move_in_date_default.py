"""remove move in date default

Revision ID: 75647fa43188
Revises: 59754fbde2b4
Create Date: 2026-08-26 00:03:09.586463

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75647fa43188'
down_revision = '59754fbde2b4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tenants", schema=None) as batch_op:
        batch_op.alter_column(
            "move_in_date",
            server_default=None
        )



def downgrade():
    with op.batch_alter_table("tenants", schema=None) as batch_op:

        batch_op.alter_column(
            "move_in_date",
            server_default=sa.text("'2026-01-01'")
        )
