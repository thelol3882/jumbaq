"""Errors that services raise. No web framework here, so the worker can use them too.

The HTTP status belongs to the class. A service picks the class and, if needed,
a more exact code:

    raise ConflictError("the case is closed", code=ErrorCode.CONFLICT)

`core/exception_handlers.py` turns them into the JSON body.
"""

from jumbaq.core.error_codes import ErrorCode


class AppError(Exception):
    status: int = 500
    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str | None = None,
        *,
        code: ErrorCode | None = None,
        field: str | None = None,
    ) -> None:
        if code is not None:
            self.code = code
        self.message = message
        # The form field the error is about, for example "kids.0.age".
        self.field = field
        super().__init__(message or self.code)


class BadRequestError(AppError):
    status = 400
    code = ErrorCode.BAD_REQUEST


class NotAuthenticatedError(AppError):
    status = 401
    code = ErrorCode.NOT_AUTHENTICATED


class ForbiddenError(AppError):
    status = 403
    code = ErrorCode.FORBIDDEN


class NotFoundError(AppError):
    status = 404
    code = ErrorCode.NOT_FOUND


class ConflictError(AppError):
    status = 409
    code = ErrorCode.CONFLICT


class TooLargeError(AppError):
    status = 413
    code = ErrorCode.TOO_LARGE


class FieldError(AppError):
    """A field is wrong, but only the database can tell, for example an unknown suspect.

    The answer looks like a validation error of pydantic:
    {"code": "common.validation_failed", "fields": {"suspect_id": "case.unknown_suspect"}}
    """

    status = 422

    def __init__(self, field: str, code: ErrorCode, message: str | None = None) -> None:
        super().__init__(message, code=code, field=field)
