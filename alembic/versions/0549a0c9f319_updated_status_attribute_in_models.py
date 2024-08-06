from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0549a0c9f319'
down_revision = '2bcc41efef28'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Define the enum type 'intensity'
    intensity_enum = sa.Enum(
        'irm%', 'max_intensity', name='intensity'
    )
    intensity_enum.create(op.get_bind(), checkfirst=True)

    # Drop the existing enum type 'status' if it exists
    op.execute("DROP TYPE IF EXISTS status CASCADE")

    op.execute("""
        UPDATE leads
        SET status = 'new'
        WHERE status NOT IN ('new', 'contacted', 'incontact', 'appointment_made', 'appointment_held', 'free_trail', 'signup_scheduled', 'no_show', 'closed_refused', 'closed_lost_contact', 'closed_disqualified', 'closed_third_party_aggregators')
    """)

    # Create new enum types
    status_enum = sa.Enum(
        'new', 'contacted', 'incontact', 'appointment_made', 'appointment_held',
        'free_trail', 'signup_scheduled', 'no_show', 'closed_refused', 
        'closed_lost_contact', 'closed_disqualified', 'closed_third_party_aggregators',
        name='status'
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    # Explicit cast using 'USING' clause for `leads` table
    op.execute("""
        ALTER TABLE leads ALTER COLUMN status TYPE status 
        USING status::text::status
    """)

    # Other column alterations
    op.alter_column('foods', 'category',
                    existing_type=postgresql.ENUM(
                        'baked_products', 'beverages', 'cheese_eggs', 'cooked_meals',
                        'fish_products', 'fruits_vegs', 'herbs_spices', 'meat_products',
                        'nuts_seeds_snacks', 'pasta_cereals', 'restaurant_meals',
                        'soups_sauces', 'sweets_candy', 'other', name='categoryenum'
                    ),
                    type_=sa.Enum(
                        'baked_products', 'beverages', 'cheese_eggs', 'cooked_meals',
                        'fish_products', 'fruits_vegs', 'herbs_spices', 'meat_products',
                        'nuts_seeds_snacks', 'pasta_cereals', 'restaurant_meals',
                        'soups_sauces', 'sweets_candy', 'other', name='__categoryenum'
                    ),
                    existing_nullable=True)

    op.alter_column('foods', 'weight_unit',
                    existing_type=postgresql.ENUM('g', 'ml', 'g_ml', name='weightunitenum'),
                    type_=sa.Enum('g', 'ml', 'g_ml', name='__weightunitenum'),
                    existing_nullable=True)

    # Add new columns
    op.add_column('events', sa.Column('price', sa.Float(), nullable=True))
    op.add_column('exercise', sa.Column('exercise_intensity', sa.Enum('irm%', 'max_intensity', name='intensity'), nullable=True))
    op.add_column('exercise', sa.Column('intensity_value', sa.Float(), nullable=True))
    
    # Alter column types and add new columns
    op.alter_column('met', 'met_value',
                    existing_type=sa.DOUBLE_PRECISION(precision=53),
                    type_=sa.String(),
                    existing_nullable=False)
    op.drop_column('met', 'met_description')
    op.add_column('workout', sa.Column('img_url', sa.String(), nullable=True))
    op.alter_column('workout', 'org_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.alter_column('workout', 'update_user_type',
                    existing_type=postgresql.ENUM('staff', 'member', 'coach', name='user_type'),
                    nullable=True)
    op.alter_column('workout', 'created_by',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.alter_column('workout', 'updated_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout', 'is_deleted',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.alter_column('workout_day', 'update_user_type',
                    existing_type=postgresql.ENUM('staff', 'member', 'coach', name='user_type'),
                    nullable=True)
    op.alter_column('workout_day', 'created_by',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.alter_column('workout_day', 'updated_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout_day', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout_day', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=False)
    op.alter_column('workout_day', 'is_deleted',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.add_column('workout_day_exercise', sa.Column('distance', sa.Float(), nullable=True))
    op.add_column('workout_day_exercise', sa.Column('speed', sa.Float(), nullable=True))
    op.add_column('workout_day_exercise', sa.Column('met_value', sa.Float(), nullable=True))
    op.alter_column('workout_day_exercise', 'intensity_type',
                    existing_type=postgresql.ENUM('max', 'irm%', name='exercise_intensity'),
                    nullable=False)
    op.alter_column('workout_day_exercise', 'update_user_type',
                    existing_type=postgresql.ENUM('staff', 'member', 'coach', name='user_type'),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'created_by',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.alter_column('workout_day_exercise', 'updated_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=False)
    op.alter_column('workout_day_exercise', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=False)
    op.alter_column('workout_day_exercise', 'is_deleted',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)

def downgrade() -> None:
    # Drop columns added in upgrade
    op.drop_column('workout_day_exercise', 'met_value')
    op.drop_column('workout_day_exercise', 'speed')
    op.drop_column('workout_day_exercise', 'distance')
    op.drop_column('workout', 'img_url')
    op.drop_column('events', 'price')
    op.drop_column('exercise', 'intensity_value')
    op.drop_column('exercise', 'exercise_intensity')

    # Revert column alterations
    op.alter_column('workout_day_exercise', 'is_deleted',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'updated_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'created_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'update_user_type',
                    existing_type=postgresql.ENUM('staff', 'member', 'coach', name='user_type'),
                    nullable=True)
    op.alter_column('workout_day_exercise', 'intensity_type',
                    existing_type=postgresql.ENUM('max', 'irm%', name='exercise_intensity'),
                    nullable=True)
    op.alter_column('workout_day', 'is_deleted',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.alter_column('workout_day', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout_day', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout_day', 'updated_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout_day', 'created_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout_day', 'update_user_type',
                    existing_type=postgresql.ENUM('staff', 'member', 'coach', name='user_type'),
                    nullable=True)
    op.alter_column('workout', 'is_deleted',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.alter_column('workout', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('workout', 'updated_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout', 'created_by',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('workout', 'update_user_type',
                    existing_type=postgresql.ENUM('staff', 'member', 'coach', name='user_type'),
                    nullable=True)
    op.alter_column('workout', 'org_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.alter_column('met', 'met_value',
                    existing_type=sa.String(),
                    nullable=True)
    op.add_column('met', sa.Column('met_description', sa.String(), nullable=True))
    op.alter_column('foods', 'weight_unit',
                    existing_type=sa.Enum('g', 'ml', 'g_ml', name='__weightunitenum'),
                    type_=postgresql.ENUM('g', 'ml', 'g_ml', name='weightunitenum'),
                    nullable=True)
    op.alter_column('foods', 'category',
                    existing_type=sa.Enum('baked_products', 'beverages', 'cheese_eggs', 'cooked_meals', 'fish_products', 'fruits_vegs', 'herbs_spices', 'meat_products', 'nuts_seeds_snacks', 'pasta_cereals', 'restaurant_meals', 'soups_sauces', 'sweets_candy', 'other', name='__categoryenum'),
                    type_=postgresql.ENUM('baked_products', 'beverages', 'cheese_eggs', 'cooked_meals', 'fish_products', 'fruits_vegs', 'herbs_spices', 'meat_products', 'nuts_seeds_snacks', 'pasta_cereals', 'restaurant_meals', 'soups_sauces', 'sweets_candy', 'other', name='categoryenum'),
                    nullable=True)
    op.alter_column('leads', 'status',
                    existing_type=sa.Enum('new', 'contacted', 'incontact', 'appointment_made', 'appointment_held', 'free_trail', 'signup_scheduled', 'no_show', 'closed_refused', 'closed_lost_contact', 'closed_disqualified', 'closed_third_party_aggregators', name='status'),
                    type_=postgresql.ENUM('new', 'contacted', 'incontact', 'appointment_made', 'appointment_held', 'free_trail', 'signup_scheduled', 'no_show', 'closed_refused', 'closed_lost_contact', 'closed_disqualified', 'closed_third_party_aggregators', name='status'),
                    nullable=True)
    op.alter_column('membership_plan', 'status',
                    existing_type=sa.Enum('active', 'inactive', 'pending', name='status'),
                    type_=sa.VARCHAR(length=10),
                    nullable=True)
    op.alter_column('facility', 'status',
                    existing_type=sa.Enum('active', 'inactive', 'pending', name='status'),
                    type_=sa.BOOLEAN(),
                    nullable=False)
    
    # Alter columns back to original state
    op.alter_column('client_organization', 'client_status',
                    existing_type=sa.VARCHAR(length=100),
                    type_=sa.Enum('active', 'inactive', name='status'),
                    nullable=True)
    
    op.alter_column('coach_organization', 'coach_status',
                    existing_type=sa.VARCHAR(length=100),
                    type_=sa.Enum('active', 'inactive', 'pending', name='status'),
                    nullable=True)
    
    # Drop the recreated enum type
    op.execute("DROP TYPE IF EXISTS status CASCADE")
    op.execute("DROP TYPE IF EXISTS intensity CASCADE")
