from uuid import UUID

"""
Default organizational role UUIDs.

These UUIDs correspond to the standard organizational roles that should be 
created in the authorization system during application bootstrap.
"""

class DefaultOrganizationRoles:
    """Standard organizational role UUIDs for foreign key references."""
    
    OWNER = UUID("00000000-0000-0000-0000-000000000001")
    ADMIN = UUID("00000000-0000-0000-0000-000000000002") 
    MEMBER = UUID("00000000-0000-0000-0000-000000000003")
    VIEWER = UUID("00000000-0000-0000-0000-000000000004")
    
    @classmethod
    def all_roles(cls) -> dict[str, UUID]:
        """Get all default role mappings."""
        return {
            "owner": cls.OWNER,
            "admin": cls.ADMIN,
            "member": cls.MEMBER,
            "viewer": cls.VIEWER,
        }
    
    @classmethod
    def get_role_uuid(cls, role_name: str) -> UUID:
        """Get UUID for a role name."""
        return cls.all_roles().get(role_name.lower(), cls.MEMBER)