"""Add constraint names to fix circular dependency

Revision ID: b57c06412a18
Revises: c6696e94e8cf_
Create Date: 2025-07-11 06:04:43.294846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b57c06412a18'
down_revision = 'c6696e94e8cf_'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing foreign key constraints
    op.drop_constraint(None, 'organizations', schema='contas', type_='foreignkey')
    op.drop_constraint(None, 'users', schema='contas', type_='foreignkey')
    
    # Add foreign key constraints with names
    op.create_foreign_key(
        'fk_organization_owner', 
        'organizations', 
        'users', 
        ['owner_id'], 
        ['id'], 
        source_schema='contas',
        referent_schema='contas'
    )
    
    op.create_foreign_key(
        'fk_user_organization', 
        'users', 
        'organizations', 
        ['organization_id'], 
        ['id'], 
        source_schema='contas',
        referent_schema='contas'
    )


def downgrade() -> None:
    # Drop named constraints
    op.drop_constraint('fk_organization_owner', 'organizations', schema='contas', type_='foreignkey')
    op.drop_constraint('fk_user_organization', 'users', schema='contas', type_='foreignkey')
    
    # Add back unnamed constraints
    op.create_foreign_key(
        None, 
        'organizations', 
        'users', 
        ['owner_id'], 
        ['id'], 
        source_schema='contas',
        referent_schema='contas'
    )
    
    op.create_foreign_key(
        None, 
        'users', 
        'organizations', 
        ['organization_id'], 
        ['id'], 
        source_schema='contas',
        referent_schema='contas'
    )