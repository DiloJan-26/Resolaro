from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from resolaro.contracts import CaseRead, CasesRead, OrganizationRead, Role
from resolaro.models import Case, Organization, OrganizationMembership


def memberships(session: Session, user_id: UUID) -> list[OrganizationRead]:
    rows = session.execute(
        select(Organization.id, Organization.name, OrganizationMembership.role)
        .join(OrganizationMembership, OrganizationMembership.organization_id == Organization.id)
        .where(OrganizationMembership.user_id == user_id)
        .order_by(Organization.name, Organization.id)
    ).all()
    return [OrganizationRead(id=id_, name=name, role=Role(role)) for id_, name, role in rows]


def membership(session: Session, user_id: UUID, organization_id: UUID) -> OrganizationRead | None:
    row = session.execute(
        select(Organization.id, Organization.name, OrganizationMembership.role)
        .join(OrganizationMembership, OrganizationMembership.organization_id == Organization.id)
        .where(OrganizationMembership.user_id == user_id, Organization.id == organization_id)
    ).one_or_none()
    return OrganizationRead(id=row[0], name=row[1], role=Role(row[2])) if row else None


def cases_for_member(session: Session, user_id: UUID, organization_id: UUID, limit: int) -> CasesRead:
    scope = (
        select(Case)
        .join(OrganizationMembership, OrganizationMembership.organization_id == Case.organization_id)
        .where(OrganizationMembership.user_id == user_id, Case.organization_id == organization_id)
    )
    items = session.scalars(scope.order_by(Case.updated_at.desc(), Case.id).limit(limit)).all()
    total = session.scalar(
        select(func.count(Case.id))
        .join(OrganizationMembership, OrganizationMembership.organization_id == Case.organization_id)
        .where(OrganizationMembership.user_id == user_id, Case.organization_id == organization_id)
    ) or 0
    return CasesRead(items=[CaseRead(id=item.id, organization_id=item.organization_id, title=item.title, status=item.status, updated_at=item.updated_at) for item in items], total=total)
