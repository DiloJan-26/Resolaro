from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Role(StrEnum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    REVIEWER = "REVIEWER"


class CaseStatus(StrEnum):
    NEW = "NEW"


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    details: dict[str, str] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    role: Role


class MeRead(BaseModel):
    user_id: UUID
    organizations: list[OrganizationRead]


class CaseCreate(BaseModel):
    """Reserved typed intake input; Phase 1 exposes no create endpoint."""

    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)


class CaseRead(BaseModel):
    id: UUID
    organization_id: UUID
    title: str
    status: CaseStatus
    updated_at: datetime


class CasesRead(BaseModel):
    items: list[CaseRead]
    total: int = Field(ge=0)
