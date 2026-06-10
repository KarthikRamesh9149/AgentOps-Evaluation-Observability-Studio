from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.errors import NotFoundError, ValidationFailure
from app.core.settings import get_settings

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


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationFailure)
async def validation_handler(_: Request, exc: ValidationFailure) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
