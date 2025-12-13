"""add activity limits

Revision ID: 7b3d1f3c8a2e
Revises: 5eae8585de48
Create Date: 2025-12-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b3d1f3c8a2e'
down_revision = '5eae8585de48'
branch_labels = None
depends_on = None


def upgrade():
    # Add daily activity limit columns to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Add integer limits with server defaults so existing rows get value 0 (prevents NULL)
        batch_op.add_column(sa.Column('daily_likes', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('daily_comments', sa.Integer(), nullable=False, server_default='0'))
        # last_activity_reset can remain nullable; set to current time for existing rows
        batch_op.add_column(sa.Column('last_activity_reset', sa.DateTime(), nullable=True))
    # Ensure existing NULL last_activity_reset values are set to now (optional)
    op.execute("UPDATE user SET last_activity_reset = CURRENT_TIMESTAMP WHERE last_activity_reset IS NULL")


def downgrade():
    # Remove the added columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_activity_reset')
        batch_op.drop_column('daily_comments')
        batch_op.drop_column('daily_likes')
