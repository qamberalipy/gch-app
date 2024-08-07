"""organization v3 table changes

Revision ID: ad87d765f9eb
Revises: c4441fabf66f
Create Date: 2024-08-07 15:38:58.873785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = 'ad87d765f9eb'
down_revision: Union[str, None] = 'c4441fabf66f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the ENUM type first
    business_type_enum = ENUM(
        'bootcamp', 'community_services', 'corporate_health', 'crossfit_box', 'dance_studio',
        'dietitian', 'educational_institute', 'fitness_center', 'hospital_clinic', 'lifestyle_coach',
        'martial_arts_center', 'online_coach', 'personal_trainer', 'personal_training_studio',
        'physiotherapy_clinic', 'yoga_pilates_studio', 'other',
        name='businesstypeenum'
    )
    business_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Add the new columns
    op.add_column('organization', sa.Column('name', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('email', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('business_type', sa.Enum('bootcamp', 'community_services', 'corporate_health', 'crossfit_box', 'dance_studio', 'dietitian', 'educational_institute', 'fitness_center', 'hospital_clinic', 'lifestyle_coach', 'martial_arts_center', 'online_coach', 'personal_trainer', 'personal_training_studio', 'physiotherapy_clinic', 'yoga_pilates_studio', 'other', name='businesstypeenum'), nullable=True))
    op.add_column('organization', sa.Column('description', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('address', sa.String(length=100), nullable=True))
    op.add_column('organization', sa.Column('zipcode', sa.String(length=10), nullable=True))
    op.add_column('organization', sa.Column('country_id', sa.Integer(), nullable=True))
    op.add_column('organization', sa.Column('city', sa.String(length=20), nullable=True))
    op.add_column('organization', sa.Column('facebook_page_url', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('website_url', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('timezone', sa.String(length=20), nullable=True))
    op.add_column('organization', sa.Column('language', sa.String(length=20), nullable=True))
    op.add_column('organization', sa.Column('company_reg_no', sa.String(length=20), nullable=True))
    op.add_column('organization', sa.Column('vat_reg_no', sa.String(length=20), nullable=True))
    op.add_column('organization', sa.Column('club_key', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('api_key', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('hide_for_nonmember', sa.Boolean(), nullable=True))
    op.add_column('organization', sa.Column('opening_hours', sa.JSON(), nullable=True))
    op.add_column('organization', sa.Column('opening_hours_notes', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('organization', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('organization', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('organization', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.drop_column('organization', 'org_name')


def downgrade() -> None:
    # Drop the new columns
    op.add_column('organization', sa.Column('org_name', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('organization', 'updated_by')
    op.drop_column('organization', 'created_by')
    op.drop_column('organization', 'updated_at')
    op.drop_column('organization', 'created_at')
    op.drop_column('organization', 'opening_hours_notes')
    op.drop_column('organization', 'opening_hours')
    op.drop_column('organization', 'hide_for_nonmember')
    op.drop_column('organization', 'api_key')
    op.drop_column('organization', 'club_key')
    op.drop_column('organization', 'vat_reg_no')
    op.drop_column('organization', 'company_reg_no')
    op.drop_column('organization', 'language')
    op.drop_column('organization', 'timezone')
    op.drop_column('organization', 'website_url')
    op.drop_column('organization', 'facebook_page_url')
    op.drop_column('organization', 'city')
    op.drop_column('organization', 'country_id')
    op.drop_column('organization', 'zipcode')
    op.drop_column('organization', 'address')
    op.drop_column('organization', 'description')
    op.drop_column('organization', 'business_type')
    op.drop_column('organization', 'email')
    op.drop_column('organization', 'name')
    
    # Drop the ENUM type
    business_type_enum = ENUM(name='businesstypeenum')
    business_type_enum.drop(op.get_bind(), checkfirst=True)
