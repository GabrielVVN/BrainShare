"""add post status

Revision ID: 8c2f9a1add
Revises: 7b3d1f3c8a2e
Create Date: 2025-12-13 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c2f9a1add'
down_revision = '7b3d1f3c8a2e'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column to post table
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))
    # Set existing rows to 'normal'
    op.execute("UPDATE post SET status='normal' WHERE status IS NULL")


def downgrade():
    # Remove status column
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_column('status')
