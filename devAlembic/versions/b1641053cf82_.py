"""empty message

Revision ID: b1641053cf82
Revises: 5ae2cfac087d
Create Date: 2024-12-16 14:12:40.482474

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1641053cf82'
down_revision: Union[str, None] = '5ae2cfac087d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'organizations_models', ['inn'])
    op.create_unique_constraint(None, 'organizations_models', ['ogrn'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'organizations_models', type_='unique')
    op.drop_constraint(None, 'organizations_models', type_='unique')
    # ### end Alembic commands ###