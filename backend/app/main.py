from __future__ import annotations

import hmac

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.errors import NotFoundError, ValidationFailure
from app.core.settings import Settings, get_settings

settings = get_settings()

app = FastAPI(title="AgentOps Evaluation & Observability Studio", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.middleware("http")
async def require_api_auth(request: Request, call_next):
    """Require a bearer token for every route except the unauthenticated liveness probe."""
    if request.url.path == "/health" or request.method == "OPTIONS":
        return await call_next(request)

    settings_provider = request.app.dependency_overrides.get(get_settings, get_settings)
    request_settings: Settings = settings_provider()
    authorization = request.headers.get("Authorization", "")
    scheme, separator, supplied_token = authorization.partition(" ")
    expected_token = request_settings.api_auth_token
    is_authorized = (
        request_settings.insecure_local_demo_enabled
        or (
            bool(expected_token)
            and bool(separator)
            and scheme.lower() == "bearer"
            and hmac.compare_digest(supplied_token, expected_token)
        )
    )
    if not is_authorized:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await call_next(request)


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationFailure)
async def validation_handler(_: Request, exc: ValidationFailure) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
