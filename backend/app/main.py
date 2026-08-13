from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.auth import authenticate_bearer, required_role
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

_request_windows: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def require_api_auth(request: Request, call_next):
    """Require a bearer token for every route except the unauthenticated liveness probe."""
    if request.url.path == "/health" or request.method == "OPTIONS":
        return await call_next(request)

    settings_provider = request.app.dependency_overrides.get(get_settings, get_settings)
    request_settings: Settings = settings_provider()
    content_length = request.headers.get("content-length")
    if content_length and (not content_length.isdigit() or int(content_length) > request_settings.max_request_bytes):
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        body = await request.body()
        if len(body) > request_settings.max_request_bytes:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})

    principal = authenticate_bearer(request.headers.get("Authorization", ""), request_settings.token_registry)
    if not request_settings.insecure_local_demo_enabled and principal is None:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    if principal is not None and principal.role not in required_role(request.method, request.url.path):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    identity = principal.token_id if principal else request.client.host if request.client else "local"
    now = time.monotonic()
    window = _request_windows[identity]
    cutoff = now - request_settings.rate_limit_window_seconds
    while window and window[0] <= cutoff:
        window.popleft()
    if len(window) >= request_settings.rate_limit_requests:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(request_settings.rate_limit_window_seconds)},
        )
    window.append(now)
    if principal is not None:
        request.state.principal = principal
    return await call_next(request)


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationFailure)
async def validation_handler(_: Request, exc: ValidationFailure) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
