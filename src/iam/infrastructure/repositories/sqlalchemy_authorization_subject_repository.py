from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func

from ...domain.entities.authorization_subject import AuthorizationSubject
from ...domain.repositories.authorization_subject_repository import AuthorizationSubjectRepository
from ..database.models import AuthorizationSubjectModel


class SqlAlchemyAuthorizationSubjectRepository(AuthorizationSubjectRepository):
    """SQLAlchemy implementation of AuthorizationSubjectRepository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, authorization_subject: AuthorizationSubject) -> AuthorizationSubject:
        """Save an authorization subject."""
        # Check if it's an existing subject (has been updated)
        existing = self._session.get(AuthorizationSubjectModel, authorization_subject.id)
        
        if existing:
            # Update existing
            existing.subject_type = authorization_subject.subject_type
            existing.subject_id = authorization_subject.subject_id
            existing.organization_id = authorization_subject.organization_id
            existing.owner_id = authorization_subject.owner_id
            existing.is_active = authorization_subject.is_active
            existing.updated_at = datetime.now(timezone.utc)
            model = existing
        else:
            # Create new
            model = AuthorizationSubjectModel(
                id=authorization_subject.id,
                subject_type=authorization_subject.subject_type,
                subject_id=authorization_subject.subject_id,
                organization_id=authorization_subject.organization_id,
                owner_id=authorization_subject.owner_id,
                is_active=authorization_subject.is_active,
            )
            self._session.add(model)
        
        try:
            self._session.flush()
            return self._model_to_entity(model)
        except IntegrityError as e:
            self._session.rollback()
            raise ValueError(f"Failed to save authorization subject: {str(e)}")

    def find_by_id(self, authorization_subject_id: UUID) -> Optional[AuthorizationSubject]:
        """Find authorization subject by ID."""
        model = self._session.get(AuthorizationSubjectModel, authorization_subject_id)
        return self._model_to_entity(model) if model else None

    def find_by_subject(
        self, subject_type: str, subject_id: UUID, organization_id: Optional[UUID] = None
    ) -> Optional[AuthorizationSubject]:
        """Find authorization subject by subject type, ID and organization."""
        query = self._session.query(AuthorizationSubjectModel).filter(
            and_(
                AuthorizationSubjectModel.subject_type == subject_type,
                AuthorizationSubjectModel.subject_id == subject_id,
                AuthorizationSubjectModel.organization_id == organization_id,
            )
        )
        
        model = query.first()
        return self._model_to_entity(model) if model else None

    def find_by_owner_id(
        self, owner_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[AuthorizationSubject]:
        """Find all authorization subjects owned by a user."""
        query = self._session.query(AuthorizationSubjectModel).filter(
            AuthorizationSubjectModel.owner_id == owner_id
        )
        
        if organization_id is not None:
            query = query.filter(AuthorizationSubjectModel.organization_id == organization_id)
        
        models = query.order_by(AuthorizationSubjectModel.created_at.desc()).all()
        return [self._model_to_entity(model) for model in models]

    def find_by_organization_id(self, organization_id: UUID) -> List[AuthorizationSubject]:
        """Find all authorization subjects in an organization."""
        models = (
            self._session.query(AuthorizationSubjectModel)
            .filter(AuthorizationSubjectModel.organization_id == organization_id)
            .order_by(AuthorizationSubjectModel.created_at.desc())
            .all()
        )
        return [self._model_to_entity(model) for model in models]

    def find_by_subject_type(
        self, subject_type: str, organization_id: Optional[UUID] = None
    ) -> List[AuthorizationSubject]:
        """Find all authorization subjects of a specific type."""
        query = self._session.query(AuthorizationSubjectModel).filter(
            AuthorizationSubjectModel.subject_type == subject_type
        )
        
        if organization_id is not None:
            query = query.filter(AuthorizationSubjectModel.organization_id == organization_id)
        
        models = query.order_by(AuthorizationSubjectModel.created_at.desc()).all()
        return [self._model_to_entity(model) for model in models]

    def find_active_by_organization(self, organization_id: UUID) -> List[AuthorizationSubject]:
        """Find all active authorization subjects in an organization."""
        models = (
            self._session.query(AuthorizationSubjectModel)
            .filter(
                and_(
                    AuthorizationSubjectModel.organization_id == organization_id,
                    AuthorizationSubjectModel.is_active == True,
                )
            )
            .order_by(AuthorizationSubjectModel.created_at.desc())
            .all()
        )
        return [self._model_to_entity(model) for model in models]

    def find_global_subjects(self) -> List[AuthorizationSubject]:
        """Find all global authorization subjects (not tied to any organization)."""
        models = (
            self._session.query(AuthorizationSubjectModel)
            .filter(AuthorizationSubjectModel.organization_id.is_(None))
            .order_by(AuthorizationSubjectModel.created_at.desc())
            .all()
        )
        return [self._model_to_entity(model) for model in models]

    def exists_subject(
        self, subject_type: str, subject_id: UUID, organization_id: Optional[UUID] = None
    ) -> bool:
        """Check if an authorization subject exists."""
        query = self._session.query(AuthorizationSubjectModel.id).filter(
            and_(
                AuthorizationSubjectModel.subject_type == subject_type,
                AuthorizationSubjectModel.subject_id == subject_id,
                AuthorizationSubjectModel.organization_id == organization_id,
            )
        )
        
        return query.first() is not None

    def delete(self, authorization_subject: AuthorizationSubject) -> bool:
        """Delete an authorization subject."""
        return self.delete_by_id(authorization_subject.id)

    def delete_by_id(self, authorization_subject_id: UUID) -> bool:
        """Delete authorization subject by ID."""
        model = self._session.get(AuthorizationSubjectModel, authorization_subject_id)
        if model:
            self._session.delete(model)
            self._session.flush()
            return True
        return False

    def count_by_owner(self, owner_id: UUID) -> int:
        """Count authorization subjects owned by a user."""
        return (
            self._session.query(AuthorizationSubjectModel)
            .filter(AuthorizationSubjectModel.owner_id == owner_id)
            .count()
        )

    def count_by_organization(self, organization_id: UUID) -> int:
        """Count authorization subjects in an organization."""
        return (
            self._session.query(AuthorizationSubjectModel)
            .filter(AuthorizationSubjectModel.organization_id == organization_id)
            .count()
        )

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[UUID] = None,
        subject_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[AuthorizationSubject]:
        """Find authorization subjects with pagination and filters."""
        query = self._session.query(AuthorizationSubjectModel)
        
        # Apply filters
        if organization_id is not None:
            query = query.filter(AuthorizationSubjectModel.organization_id == organization_id)
        
        if subject_type is not None:
            query = query.filter(AuthorizationSubjectModel.subject_type == subject_type)
        
        if is_active is not None:
            query = query.filter(AuthorizationSubjectModel.is_active == is_active)
        
        # Apply pagination and ordering
        models = (
            query.order_by(AuthorizationSubjectModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [self._model_to_entity(model) for model in models]

    def bulk_update_organization(
        self, subject_ids: List[UUID], new_organization_id: Optional[UUID]
    ) -> int:
        """Bulk update organization for multiple subjects."""
        if not subject_ids:
            return 0
        
        updated_count = (
            self._session.query(AuthorizationSubjectModel)
            .filter(AuthorizationSubjectModel.id.in_(subject_ids))
            .update(
                {
                    "organization_id": new_organization_id,
                    "updated_at": datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        
        self._session.flush()
        return updated_count

    def bulk_update_owner(self, subject_ids: List[UUID], new_owner_id: UUID) -> int:
        """Bulk update owner for multiple subjects."""
        if not subject_ids:
            return 0
        
        updated_count = (
            self._session.query(AuthorizationSubjectModel)
            .filter(AuthorizationSubjectModel.id.in_(subject_ids))
            .update(
                {
                    "owner_id": new_owner_id,
                    "updated_at": datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        
        self._session.flush()
        return updated_count

    def bulk_activate(self, subject_ids: List[UUID]) -> int:
        """Bulk activate multiple authorization subjects."""
        if not subject_ids:
            return 0
        
        updated_count = (
            self._session.query(AuthorizationSubjectModel)
            .filter(
                and_(
                    AuthorizationSubjectModel.id.in_(subject_ids),
                    AuthorizationSubjectModel.is_active == False,
                )
            )
            .update(
                {
                    "is_active": True,
                    "updated_at": datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        
        self._session.flush()
        return updated_count

    def bulk_deactivate(self, subject_ids: List[UUID]) -> int:
        """Bulk deactivate multiple authorization subjects."""
        if not subject_ids:
            return 0
        
        updated_count = (
            self._session.query(AuthorizationSubjectModel)
            .filter(
                and_(
                    AuthorizationSubjectModel.id.in_(subject_ids),
                    AuthorizationSubjectModel.is_active == True,
                )
            )
            .update(
                {
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        
        self._session.flush()
        return updated_count

    def _model_to_entity(self, model: AuthorizationSubjectModel) -> AuthorizationSubject:
        """Convert database model to domain entity."""
        return AuthorizationSubject(
            id=model.id,
            subject_type=model.subject_type,
            subject_id=model.subject_id,
            organization_id=model.organization_id,
            owner_id=model.owner_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )