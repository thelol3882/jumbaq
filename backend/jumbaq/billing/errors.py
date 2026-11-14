from jumbaq.core.error_codes import ErrorCode
from jumbaq.core.errors import AppError, BadRequestError, ConflictError


class PaymentRequiredError(AppError):
    status = 402
    code = ErrorCode.BILLING_PAYMENT_REQUIRED


class AlreadySubscribedError(ConflictError):
    code = ErrorCode.BILLING_ALREADY_SUBSCRIBED


class BadSignatureError(BadRequestError):
    """The webhook body is not signed by the payment provider with our secret."""

    code = ErrorCode.BILLING_BAD_SIGNATURE


class BillingNotConfiguredError(AppError):
    status = 503
    code = ErrorCode.BILLING_NOT_CONFIGURED


class BillingUnavailableError(AppError):
    """The payment provider is down or slow. The parent can press the button again."""

    status = 503
    code = ErrorCode.BILLING_UNAVAILABLE
