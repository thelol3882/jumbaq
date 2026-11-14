from jumbaq.core.error_codes import ErrorCode
from jumbaq.core.errors import AppError


class AiDailyLimitError(AppError):
    status = 429
    code = ErrorCode.AI_DAILY_LIMIT_REACHED


class AiBadOutputError(AppError):
    """Permanent for this call: a refusal, a cut answer or JSON of the wrong shape.

    Trying the same request again later does not help, so the caller decides: retry once now
    or use its fallback.
    """

    code = ErrorCode.AI_BAD_OUTPUT


class AiUnavailableError(AppError):
    """Temporary: a timeout, a network error, a 429 or a 5xx of the provider. A handler lets it
    go up, so the outbox tries the event again later."""

    status = 503
    code = ErrorCode.AI_UNAVAILABLE
