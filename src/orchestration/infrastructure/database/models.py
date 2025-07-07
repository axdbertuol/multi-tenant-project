from sqlalchemy import Column, String, DateTime, Text, Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from ...domain.entities import OnboardingStatus

Base = declarative_base()


class OnboardingWorkflowModel(Base):
    __tablename__ = "onboarding_workflows"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    plan_id = Column(String(36), nullable=False)
    status = Column(SqlEnum(OnboardingStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)