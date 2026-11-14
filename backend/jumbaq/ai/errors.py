from jumbaq.core.error_codes import ErrorCode
from jumbaq.core.errors import AppError, BadRequestError


class AiDailyLimitError(AppError):
    status = 429
    code = ErrorCode.AI_DAILY_LIMIT_REACHED


class AiDisabledError(AppError):
    """The owner switched the model off. Like the daily cap, a caller uses its built-in story."""

    status = 503
    code = ErrorCode.AI_DISABLED


class AiLimitInvalidError(BadRequestError):
    """The daily cap set by the owner cannot be negative."""


class AiBadOutputError(AppError):
    """Permanent for this call: a refusal, a cut answer or JSON of the wrong shape.

    Trying the same request again later does not help, so the caller decides: retry once now
    or use its fallback.
    """

    code = ErrorCode.AI_BAD_OUTPUT


class AiUnavailableError(AppError):
    """A temporary failure: a timeout, a network error, a 429 or a 5xx of the provider. A handler
    lets it go up, so the outbox tries the event again later."""

    status = 503
    code = ErrorCode.AI_UNAVAILABLE
