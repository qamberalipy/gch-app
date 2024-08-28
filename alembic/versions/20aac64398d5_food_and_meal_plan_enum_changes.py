"""Food and Meal Plan Enum changes

Revision ID: 20aac64398d5
Revises: 117bc4d0bda5
Create Date: 2024-08-28 16:31:17.927788

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20aac64398d5'
down_revision: Union[str, None] = '117bc4d0bda5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the new enum type
new_visiblefor_enum = postgresql.ENUM(
    'only_myself', 
    'coaches', 
    'members', 
    'everyone', 
    name='visibleforenum'
)

def upgrade() -> None:
    # Create the new enum type
    new_visiblefor_enum.create(op.get_bind(), checkfirst=True)

    # Drop the existing 'visible_for' column
    op.drop_column('foods', 'visible_for')
    op.drop_column('meal_plan', 'visible_for')

    # Add the 'visible_for' column with the new enum type and set a default value
    op.add_column('foods', sa.Column('visible_for', new_visiblefor_enum, nullable=False, server_default='everyone'))
    op.add_column('meal_plan', sa.Column('visible_for', new_visiblefor_enum, nullable=False, server_default='everyone'))

def downgrade() -> None:
    # Drop the 'visible_for' column with the new enum type
    op.drop_column('foods', 'visible_for')
    op.drop_column('meal_plan', 'visible_for')
    
    # Recreate the old enum type
    old_visiblefor_enum = postgresql.ENUM(
        'old_value_1', 
        'old_value_2', 
        name='visibleforenum_old'
    )
    old_visiblefor_enum.create(op.get_bind(), checkfirst=True)

    # Add the 'visible_for' column with the old enum type
    op.add_column('foods', sa.Column('visible_for', old_visiblefor_enum, nullable=True))
    op.add_column('meal_plan', sa.Column('visible_for', old_visiblefor_enum, nullable=True))

    # Drop the new enum type
    op.execute("DROP TYPE IF EXISTS visibleforenum CASCADE")
