from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from resolaro import auth
from resolaro.errors import ApiError
from resolaro.settings import Settings


def test_jwt_checks_signature_issuer_audience_and_expiry(monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(auth, "jwks_client", lambda url: SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=private.public_key())))
    settings = Settings(database_url="postgresql://user:pass@host/db", supabase_url="https://example.supabase.co", cors_origins="https://example.pages.dev")
    now = datetime.now(timezone.utc)
    claims = {"sub": str(uuid4()), "iss": "https://example.supabase.co/auth/v1", "aud": "authenticated", "iat": now, "exp": now + timedelta(minutes=5)}
    token = jwt.encode(claims, private, algorithm="RS256", headers={"kid": "test"})
    assert str(auth.verify_token(token, settings).user_id) == claims["sub"]
    for changed in (
        {"iss": "https://other.supabase.co/auth/v1"},
        {"aud": "other"},
        {"exp": now - timedelta(minutes=5)},
    ):
        with pytest.raises(ApiError) as error:
            auth.verify_token(jwt.encode({**claims, **changed}, private, algorithm="RS256", headers={"kid": "test"}), settings)
        assert error.value.status_code == 401
    forged = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(ApiError):
        auth.verify_token(jwt.encode(claims, forged, algorithm="RS256", headers={"kid": "test"}), settings)
