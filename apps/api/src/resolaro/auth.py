from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKClientConnectionError, PyJWTError

from resolaro.settings import Settings, get_settings

bearer = HTTPBearer(auto_error=False)
ALGORITHMS = ["ES256", "RS256"]


@dataclass(frozen=True)
class Identity:
    user_id: UUID


@lru_cache(maxsize=8)
def jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(f"{url}/auth/v1/.well-known/jwks.json", cache_jwk_set=True, lifespan=300, timeout=5)


def verify_token(token: str, settings: Settings) -> Identity:
    from resolaro.errors import ApiError

    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") not in ALGORITHMS or not header.get("kid"):
            raise ApiError(401, "INVALID_TOKEN", "Session is invalid or expired")
        key = jwks_client(settings.supabase_url).get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS,
            audience=settings.supabase_jwt_audience,
            issuer=f"{settings.supabase_url}/auth/v1",
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            leeway=30,
        )
        return Identity(user_id=UUID(claims["sub"]))
    except ApiError:
        raise
    except PyJWKClientConnectionError as exc:
        raise ApiError(503, "AUTH_PROVIDER_UNAVAILABLE", "Authentication is temporarily unavailable") from exc
    except (PyJWTError, ValueError, KeyError, TypeError) as exc:
        raise ApiError(401, "INVALID_TOKEN", "Session is invalid or expired") from exc


def get_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
) -> Identity:
    from resolaro.errors import ApiError

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(401, "AUTH_REQUIRED", "Sign in to continue")
    return verify_token(credentials.credentials, settings)
