"""add user id to Transactions

Revision ID: 0440c0003780
Revises: 3f54a39b1b50
Create Date: 2023-04-05 17:07:00.106123

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0440c0003780'
down_revision = '3f54a39b1b50'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###