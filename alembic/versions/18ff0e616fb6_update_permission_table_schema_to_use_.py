"""update permission table schema to use action and resource_type fields

Revision ID: 18ff0e616fb6
Revises: 0db660442dab
Create Date: 2025-06-29 22:59:18.902778

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '18ff0e616fb6'
down_revision = '0db660442dab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create authorization permissions table with new schema
    op.create_table('authorization_permissions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('action', sa.Enum('CREATE', 'READ', 'UPDATE', 'DELETE', 'EXECUTE', 'MANAGE', name='permissionactionenum'), nullable=False),
    sa.Column('resource_type', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_system_permission', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'resource_type')
    )
    op.create_index(op.f('ix_authorization_permissions_action'), 'authorization_permissions', ['action'], unique=False)
    op.create_index(op.f('ix_authorization_permissions_name'), 'authorization_permissions', ['name'], unique=False)
    op.create_index(op.f('ix_authorization_permissions_resource_type'), 'authorization_permissions', ['resource_type'], unique=False)
    
    # Create authorization roles table
    op.create_table('authorization_roles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=True),
    sa.Column('parent_role_id', sa.UUID(), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_system_role', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['parent_role_id'], ['authorization_roles.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'organization_id')
    )
    op.create_index(op.f('ix_authorization_roles_name'), 'authorization_roles', ['name'], unique=False)
    op.create_index(op.f('ix_authorization_roles_organization_id'), 'authorization_roles', ['organization_id'], unique=False)
    op.create_index(op.f('ix_authorization_roles_parent_role_id'), 'authorization_roles', ['parent_role_id'], unique=False)
    
    # Create authorization policies table
    op.create_table('authorization_policies',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('effect', sa.Enum('ALLOW', 'DENY', name='policyeffectenum'), nullable=False),
    sa.Column('resource_type', sa.String(length=50), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('conditions', sa.JSON(), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_policy_lookup', 'authorization_policies', ['resource_type', 'action', 'organization_id'], unique=False)
    op.create_index(op.f('ix_authorization_policies_effect'), 'authorization_policies', ['effect'], unique=False)
    op.create_index(op.f('ix_authorization_policies_name'), 'authorization_policies', ['name'], unique=False)
    op.create_index(op.f('ix_authorization_policies_organization_id'), 'authorization_policies', ['organization_id'], unique=False)
    op.create_index(op.f('ix_authorization_policies_resource_type'), 'authorization_policies', ['resource_type'], unique=False)
    
    # Create role permissions association table
    op.create_table('role_permissions',
    sa.Column('role_id', sa.UUID(), nullable=False),
    sa.Column('permission_id', sa.UUID(), nullable=False),
    sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['authorization_permissions.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['authorization_roles.id'], ),
    sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Create user role assignments table
    op.create_table('user_role_assignments',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('role_id', sa.UUID(), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=True),
    sa.Column('assigned_by', sa.UUID(), nullable=False),
    sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['authorization_roles.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    
    # Drop old permissions table if it exists
    op.drop_table('permissions', schema='contas')
    op.drop_table('roles', schema='contas')
    op.drop_table('role_permissions', schema='contas')
    op.drop_table('user_organization_roles', schema='contas')


def downgrade() -> None:
    # Drop new authorization tables
    op.drop_table('user_role_assignments')
    op.drop_table('role_permissions')
    op.drop_index('ix_policy_lookup', table_name='authorization_policies')
    op.drop_table('authorization_policies')
    op.drop_table('authorization_roles')
    op.drop_table('authorization_permissions')
    
    # Recreate old tables
    op.create_table('permissions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('resource', sa.String(length=255), nullable=False),
    sa.Column('action', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='contas'
    )
    
    op.create_table('roles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_system', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='contas'
    )