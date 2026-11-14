from enum import StrEnum


class ErrorCode(StrEnum):
    """Every error code the API can return.

    The web app uses the values as translation keys, so a value never changes once it is used.
    Codes of a module are added here when the module is built.
    """

    # common
    BAD_REQUEST = "common.bad_request"
    NOT_FOUND = "common.not_found"
    METHOD_NOT_ALLOWED = "common.method_not_allowed"
    CONFLICT = "common.conflict"
    TOO_LARGE = "common.too_large"
    TOO_MANY_REQUESTS = "common.too_many_requests"
    VALIDATION_FAILED = "common.validation_failed"
    HTTP_ERROR = "common.http_error"
    INTERNAL_ERROR = "common.internal_error"
    NOT_AUTHENTICATED = "common.not_authenticated"
    FORBIDDEN = "common.forbidden"

    # families
    # No family session cookie, or one that no family has. The web app starts the setup.
    FAMILY_NO_SESSION = "family.no_session"
    FAMILY_KID_NICKNAME_REPEATED = "family.kid_nickname_repeated"
