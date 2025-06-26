from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from domain.entities.organization import Organization
from domain.repositories.organization_repository import OrganizationRepository
from infrastructure.database.models import OrganizationModel, user_organization_association
from infrastructure.repositories.base_sqlalchemy_repository import SQLAlchemyRepository


class OrganizationRepositoryImpl(SQLAlchemyRepository[Organization, OrganizationModel], OrganizationRepository):
    def __init__(self, db: Session):
        super().__init__(db, OrganizationModel)

    def _to_domain(self, model: OrganizationModel) -> Organization:
        return Organization(
            id=model.id,
            name=model.name,
            description=model.description,
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
        )

    def _to_model(self, organization: Organization) -> OrganizationModel:
        return OrganizationModel(
            id=organization.id,
            name=organization.name,
            description=organization.description,
            owner_id=organization.owner_id,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            is_active=organization.is_active,
        )

    def _update_model(self, model: OrganizationModel, organization: Organization) -> OrganizationModel:
        model.name = organization.name
        model.description = organization.description
        model.owner_id = organization.owner_id
        model.updated_at = organization.updated_at
        model.is_active = organization.is_active
        return model

    async def get_by_name(self, name: str) -> Optional[Organization]:
        model = self.db.query(OrganizationModel).filter(OrganizationModel.name == name).first()
        return self._to_domain(model) if model else None

    async def get_by_owner_id(self, owner_id: UUID) -> List[Organization]:
        models = self.db.query(OrganizationModel).filter(OrganizationModel.owner_id == owner_id).all()
        return [self._to_domain(model) for model in models]

    async def get_organizations_by_user_id(self, user_id: UUID) -> List[Organization]:
        models = (
            self.db.query(OrganizationModel)
            .join(user_organization_association)
            .filter(user_organization_association.c.user_id == user_id)
            .all()
        )
        return [self._to_domain(model) for model in models]

    async def add_user_to_organization(self, organization_id: UUID, user_id: UUID) -> None:
        insert_stmt = user_organization_association.insert().values(
            user_id=user_id,
            organization_id=organization_id
        )
        self.db.execute(insert_stmt)

    async def remove_user_from_organization(self, organization_id: UUID, user_id: UUID) -> None:
        delete_stmt = user_organization_association.delete().where(
            and_(
                user_organization_association.c.user_id == user_id,
                user_organization_association.c.organization_id == organization_id
            )
        )
        self.db.execute(delete_stmt)

    async def is_user_in_organization(self, organization_id: UUID, user_id: UUID) -> bool:
        result = self.db.query(user_organization_association).filter(
            and_(
                user_organization_association.c.user_id == user_id,
                user_organization_association.c.organization_id == organization_id
            )
        ).first()
        return result is not None