"""Map domain errors to HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.cad_types import CadError
from app.services.design_turn import DesignTurnError
from app.services.template_library import TemplateError

_NOT_FOUND_MARKERS = ("不存在", "not found")


def _status_for_message(exc: Exception, *, default: int = 400) -> int:
    message = str(exc).lower()
    if any(marker in message for marker in _NOT_FOUND_MARKERS):
        return 404
    return default


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DesignTurnError)
    async def design_turn_error(_request: Request, exc: DesignTurnError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(CadError)
    async def cad_error(_request: Request, exc: CadError) -> JSONResponse:
        status = _status_for_message(exc)
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    @app.exception_handler(TemplateError)
    async def template_error(_request: Request, exc: TemplateError) -> JSONResponse:
        status = _status_for_message(exc)
        return JSONResponse(status_code=status, content={"detail": str(exc)})
