"""The only place that turns exceptions into the JSON error body.

    {"error": {"code": "common.not_found", "request_id": "...", "message": "..."}}

`code` is a translation key, `message` is only for developers, and `fields`
maps a form field to a code.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from jumbaq.core.error_codes import ErrorCode
from jumbaq.core.errors import AppError, FieldError
from jumbaq.core.middleware import REQUEST_ID_HEADER

_CODES_BY_STATUS = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.NOT_AUTHENTICATED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    409: ErrorCode.CONFLICT,
    413: ErrorCode.TOO_LARGE,
    429: ErrorCode.TOO_MANY_REQUESTS,
}

# Where a value came from in the request. Not part of the field name.
_LOCATIONS = {"body", "query", "path", "header", "cookie"}
_VALUE_ERROR_PREFIX = "Value error, "


def _request_id(request: Request) -> str:
    # The middleware puts the id in the scope state, so it is there even for the
    # 500 handler, which runs after the middleware has finished.
    return getattr(request.state, "request_id", "-")


def _error_response(
    request: Request,
    status: int,
    code: ErrorCode,
    message: str | None = None,
    fields: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "request_id": _request_id(request)}
    if message:
        body["message"] = message
    if fields:
        body["fields"] = fields
    return JSONResponse({"error": body}, status_code=status, headers=headers)


def _field_name(loc: tuple[int | str, ...]) -> str:
    parts = loc[1:] if loc and loc[0] in _LOCATIONS else loc
    return ".".join(str(part) for part in parts) or str(loc[0])


def _field_code(err: dict[str, Any]) -> str:
    """Pydantic error type, like "missing" or "string_too_short".

    Our own validators raise ValueError with a translation key ("family.kid_nickname_repeated"),
    so for them we return that key without the "Value error, " prefix.
    """
    if err["type"] == "value_error":
        return err["msg"].removeprefix(_VALUE_ERROR_PREFIX)
    return err["type"]


async def _app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    fields = {exc.field: exc.code.value} if exc.field else None
    # A 422 looks the same as a pydantic validation error: the exact code is in `fields`.
    code = ErrorCode.VALIDATION_FAILED if isinstance(exc, FieldError) else exc.code
    return _error_response(request, exc.status, code, exc.message, fields)


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _CODES_BY_STATUS.get(exc.status_code, ErrorCode.HTTP_ERROR)
    message = exc.detail if isinstance(exc.detail, str) else None
    return _error_response(request, exc.status_code, code, message, headers=exc.headers)


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    fields: dict[str, str] = {}
    for err in exc.errors():
        # Only the first error of each field.
        fields.setdefault(_field_name(tuple(err["loc"])), _field_code(err))
    return _error_response(request, 422, ErrorCode.VALIDATION_FAILED, fields=fields)


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    # Starlette calls this outside of our middleware, so the middleware has already
    # logged the error with the request id, and here we add the header ourselves.
    request_id = _request_id(request)
    return _error_response(
        request, 500, ErrorCode.INTERNAL_ERROR, headers={REQUEST_ID_HEADER: request_id}
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unhandled_error)
