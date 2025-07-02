from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query


from ..dependencies import get_role_use_case
from ...application.use_cases.role_use_cases import RoleUseCase
from ...application.dtos.role_dto import (
    RoleCreateDTO,
    RoleUpdateDTO,
    RoleResponseDTO,
    RoleDetailResponseDTO,
    RoleListResponseDTO,
    RolePermissionAssignDTO,
    RolePermissionRemoveDTO,
    RoleInheritanceDTO,
    RoleHierarchyResponseDTO,
)
from ...application.dtos.permission_dto import PermissionResponseDTO

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RoleResponseDTO, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreateDTO,
    created_by: UUID = Query(..., description="User ID who is creating the role"),
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Create a new role with optional parent for inheritance."""
    try:
        return role_use_case.create_role(role_data, created_by)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{role_id}", response_model=RoleDetailResponseDTO)
def get_role(
    role_id: UUID,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Get role by ID with permissions."""
    role = role_use_case.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return role


@router.put("/{role_id}", response_model=RoleResponseDTO)
def update_role(
    role_id: UUID,
    role_data: RoleUpdateDTO,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Update an existing role."""
    try:
        role = role_use_case.update_role(role_id, role_data)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        return role
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: UUID,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Delete a role (soft delete)."""
    try:
        success = role_use_case.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/", response_model=RoleListResponseDTO)
def list_roles(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_system: bool = Query(True, description="Include system roles"),
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """List roles with pagination."""
    try:
        return role_use_case.list_roles(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            include_system=include_system,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{role_id}/permissions", response_model=RoleDetailResponseDTO)
def assign_permissions(
    role_id: UUID,
    permission_data: RolePermissionAssignDTO,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Assign permissions to a role."""
    try:
        role = role_use_case.assign_permissions(role_id, permission_data)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        return role
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{role_id}/permissions", response_model=RoleDetailResponseDTO)
def remove_permissions(
    role_id: UUID,
    permission_data: RolePermissionRemoveDTO,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Remove permissions from a role."""
    try:
        role = role_use_case.remove_permissions(role_id, permission_data)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        return role
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Role Inheritance Endpoints


@router.put("/{role_id}/parent", response_model=RoleResponseDTO)
def set_role_parent(
    role_id: UUID,
    inheritance_data: RoleInheritanceDTO,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Set parent role for inheritance."""
    try:
        role = role_use_case.set_role_parent(role_id, inheritance_data.parent_role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        return role
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{role_id}/parent", response_model=RoleResponseDTO)
def remove_role_parent(
    role_id: UUID,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Remove parent role inheritance."""
    try:
        role = role_use_case.remove_role_parent(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        return role
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/hierarchy/", response_model=List[RoleResponseDTO])
def get_role_hierarchy(
    organization_id: Optional[UUID] = Query(None, description="Organization ID"),
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Get role hierarchy for an organization."""
    try:
        return role_use_case.get_role_hierarchy(organization_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{role_id}/children", response_model=List[RoleResponseDTO])
def get_role_children(
    role_id: UUID,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Get direct child roles of a role."""
    try:
        return role_use_case.get_role_children(role_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{role_id}/effective-permissions", response_model=List[PermissionResponseDTO]
)
def get_effective_permissions(
    role_id: UUID,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Get all effective permissions for a role (including inherited)."""
    try:
        return role_use_case.get_effective_permissions(role_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/hierarchy/tree", response_model=dict)
def get_role_tree(
    organization_id: Optional[UUID] = Query(None, description="Organization ID"),
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Get role hierarchy as tree structure."""
    try:
        return role_use_case.get_role_tree(organization_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/hierarchy/validate", response_model=List[str])
def validate_role_hierarchy(
    organization_id: Optional[UUID] = Query(None, description="Organization ID"),
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Validate role hierarchy for issues."""
    try:
        return role_use_case.validate_role_hierarchy(organization_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/organization/{organization_id}", response_model=List[RoleResponseDTO])
def get_roles_by_organization(
    organization_id: UUID,
    role_use_case: RoleUseCase = Depends(get_role_use_case),
):
    """Get all roles for an organization."""
    try:
        return role_use_case.get_roles_by_organization(organization_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
