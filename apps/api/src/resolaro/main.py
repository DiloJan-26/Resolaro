import json
import logging
import uuid

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from resolaro.auth import Identity, get_identity
from resolaro.contracts import CasesRead, ErrorBody, ErrorEnvelope, MeRead, OrganizationRead
from resolaro.database import get_session
from resolaro.errors import ApiError
from resolaro.repository import cases_for_member, membership, memberships
from resolaro.settings import Settings, get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("resolaro")


def envelope(request: Request, code: str, message: str) -> dict:
    return ErrorEnvelope(error=ErrorBody(code=code, message=message, request_id=request.state.request_id)).model_dump()


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    app = FastAPI(title="Resolaro API", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=config.allowed_origins, allow_methods=["GET"], allow_headers=["Authorization", "Content-Type"], expose_headers=["X-Request-ID"])

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        try:
            response = await call_next(request)
        except SQLAlchemyError:
            logger.error(json.dumps({"event": "database_error", "request_id": request.state.request_id}))
            response = JSONResponse(status_code=503, content=envelope(request, "DATABASE_UNAVAILABLE", "Service temporarily unavailable"))
        except Exception:
            logger.error(json.dumps({"event": "unhandled_error", "request_id": request.state.request_id}))
            response = JSONResponse(status_code=500, content=envelope(request, "INTERNAL_ERROR", "Unexpected server error"))
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info(json.dumps({"event": "request", "request_id": request.state.request_id, "method": request.method, "path": request.url.path, "status": response.status_code}))
        return response

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content=envelope(request, exc.code, exc.message), headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content=envelope(request, "VALIDATION_ERROR", "Request is invalid"))

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logger.error(json.dumps({"event": "database_error", "request_id": request.state.request_id}))
        return JSONResponse(status_code=503, content=envelope(request, "DATABASE_UNAVAILABLE", "Service temporarily unavailable"))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content=envelope(request, "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR", "Resource unavailable"))

    @app.get("/healthz", tags=["health"])
    def healthz():
        return {"status": "ok"}

    @app.get("/api/v1/me", response_model=MeRead, tags=["identity"])
    def me(identity: Identity = Depends(get_identity), session: Session = Depends(get_session)):
        return MeRead(user_id=identity.user_id, organizations=memberships(session, identity.user_id))

    @app.get("/api/v1/organizations/{organization_id}/context", response_model=OrganizationRead, tags=["organizations"])
    def organization_context(organization_id: uuid.UUID, identity: Identity = Depends(get_identity), session: Session = Depends(get_session)):
        result = membership(session, identity.user_id, organization_id)
        if result is None:
            raise ApiError(404, "ORGANIZATION_NOT_FOUND", "Organization unavailable")
        return result

    @app.get("/api/v1/cases", response_model=CasesRead, tags=["cases"])
    def list_cases(organization_id: uuid.UUID, limit: int = Query(default=20, ge=1, le=100), identity: Identity = Depends(get_identity), session: Session = Depends(get_session)):
        if membership(session, identity.user_id, organization_id) is None:
            raise ApiError(404, "ORGANIZATION_NOT_FOUND", "Organization unavailable")
        return cases_for_member(session, identity.user_id, organization_id, limit)

    return app


app = create_app()
