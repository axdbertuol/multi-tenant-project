"""migrate_user_organization_roles_to_fk

Revision ID: 360c80c57912
Revises: 18ff0e616fb6
Create Date: 2025-06-30 21:38:10.141841

Migrate user_organization_roles table from enum-based roles to foreign key based roles.
This enables dynamic role management and leverages the existing authorization.roles infrastructure.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '360c80c57912'
down_revision = '18ff0e616fb6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade to FK-based roles."""
    
    # Step 1: Create default organizational roles in the roles table if they don't exist
    op.execute("""
    INSERT INTO contas.roles (id, name, description, is_active, is_system, organization_id, created_at, updated_at)
    VALUES 
        ('00000000-0000-0000-0000-000000000001', 'owner', 'Organization Owner - Full Control', true, true, null, NOW(), NOW()),
        ('00000000-0000-0000-0000-000000000002', 'admin', 'Organization Administrator', true, true, null, NOW(), NOW()),
        ('00000000-0000-0000-0000-000000000003', 'member', 'Organization Member', true, true, null, NOW(), NOW()),
        ('00000000-0000-0000-0000-000000000004', 'viewer', 'Organization Viewer - Read Only', true, true, null, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING;
    """)
    
    # Step 2: Add new columns
    op.add_column('user_organization_roles', sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('user_organization_roles', sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_organization_roles', sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_organization_roles', sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Step 3: Migrate existing data from enum to role_id
    op.execute("""
    UPDATE contas.user_organization_roles 
    SET role_id = CASE 
        WHEN role = 'owner' THEN '00000000-0000-0000-0000-000000000001'::uuid
        WHEN role = 'admin' THEN '00000000-0000-0000-0000-000000000002'::uuid
        WHEN role = 'member' THEN '00000000-0000-0000-0000-000000000003'::uuid
        WHEN role = 'viewer' THEN '00000000-0000-0000-0000-000000000004'::uuid
        ELSE '00000000-0000-0000-0000-000000000003'::uuid  -- default to member
    END,
    assigned_at = COALESCE(created_at, NOW())
    WHERE role_id IS NULL;
    """)
    
    # Step 4: Make role_id and assigned_at NOT NULL after migration
    op.alter_column('user_organization_roles', 'role_id', nullable=False)
    op.alter_column('user_organization_roles', 'assigned_at', nullable=False)
    
    # Step 5: Add foreign key constraint
    op.create_foreign_key(
        'fk_user_organization_roles_role_id',
        'user_organization_roles', 'roles',
        ['role_id'], ['id']
    )
    
    # Step 6: Add foreign key constraint for revoked_by
    op.create_foreign_key(
        'fk_user_organization_roles_revoked_by',
        'user_organization_roles', 'users',
        ['revoked_by'], ['id']
    )
    
    # Step 7: Add indexes for performance
    op.create_index('idx_user_organization_roles_role_id', 'user_organization_roles', ['role_id'])
    op.create_index('idx_user_organization_roles_assigned_at', 'user_organization_roles', ['assigned_at'])
    
    # Step 8: Drop the old enum column (after ensuring data is migrated)
    op.drop_column('user_organization_roles', 'role')


def downgrade() -> None:
    """Downgrade back to enum-based roles."""
    
    # Step 1: Re-add the enum type and column
    role_enum = postgresql.ENUM('owner', 'admin', 'member', 'viewer', name='organizationroleenum')
    role_enum.create(op.get_bind())
    
    op.add_column('user_organization_roles', sa.Column('role', role_enum, nullable=True))
    
    # Step 2: Migrate data back from role_id to enum
    op.execute("""
    UPDATE contas.user_organization_roles 
    SET role = CASE 
        WHEN role_id = '00000000-0000-0000-0000-000000000001'::uuid THEN 'owner'::organizationroleenum
        WHEN role_id = '00000000-0000-0000-0000-000000000002'::uuid THEN 'admin'::organizationroleenum
        WHEN role_id = '00000000-0000-0000-0000-000000000003'::uuid THEN 'member'::organizationroleenum
        WHEN role_id = '00000000-0000-0000-0000-000000000004'::uuid THEN 'viewer'::organizationroleenum
        ELSE 'member'::organizationroleenum
    END
    WHERE role IS NULL;
    """)
    
    # Step 3: Make role NOT NULL after migration
    op.alter_column('user_organization_roles', 'role', nullable=False)
    
    # Step 4: Drop new columns and constraints
    op.drop_index('idx_user_organization_roles_assigned_at', 'user_organization_roles')
    op.drop_index('idx_user_organization_roles_role_id', 'user_organization_roles')
    op.drop_constraint('fk_user_organization_roles_revoked_by', 'user_organization_roles', type_='foreignkey')
    op.drop_constraint('fk_user_organization_roles_role_id', 'user_organization_roles', type_='foreignkey')
    
    op.drop_column('user_organization_roles', 'revoked_by')
    op.drop_column('user_organization_roles', 'revoked_at')
    op.drop_column('user_organization_roles', 'assigned_at')
    op.drop_column('user_organization_roles', 'role_id')