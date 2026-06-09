from __future__ import annotations

from fastapi import HTTPException


class NotFoundError(Exception):
    pass


class ValidationFailure(Exception):
    pass


def http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValidationFailure):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected local application error")
