import pytest
from pydantic import ValidationError

from resolaro.contracts import CaseCreate
from resolaro.settings import Settings


def test_case_create_rejects_extra_fields():
    with pytest.raises(ValidationError):
        CaseCreate(title="Case", organization_id="caller-provided")


def test_settings_rejects_insecure_auth_origin():
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql://user:pass@host/db", supabase_url="http://host", cors_origins="https://example.pages.dev")
