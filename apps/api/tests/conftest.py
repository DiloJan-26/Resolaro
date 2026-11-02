import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "postgresql://demo:demo@localhost:5432/demo")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("CORS_ORIGINS", "https://example.pages.dev")

from resolaro.auth import Identity, get_identity  # noqa: E402
from resolaro.database import get_session  # noqa: E402
from resolaro.main import app  # noqa: E402
from resolaro.models import Base, Case, Organization, OrganizationMembership  # noqa: E402


@pytest.fixture
def sample():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    user_id, other_user = uuid.uuid4(), uuid.uuid4()
    org_id, other_org = uuid.uuid4(), uuid.uuid4()
    with Session(engine) as session:
        session.add_all([
            Organization(id=org_id, name="Demo"),
            Organization(id=other_org, name="Other"),
            OrganizationMembership(organization_id=org_id, user_id=user_id, role="OPERATOR"),
            OrganizationMembership(organization_id=other_org, user_id=other_user, role="ADMIN"),
            Case(organization_id=org_id, title="Allowed case"),
            Case(organization_id=other_org, title="Private case"),
        ])
        session.commit()

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    with TestClient(app) as client:
        yield client, user_id, org_id, other_org
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def signed_in(sample):
    client, user_id, org_id, other_org = sample
    app.dependency_overrides[get_identity] = lambda: Identity(user_id=user_id)
    return client, user_id, org_id, other_org
