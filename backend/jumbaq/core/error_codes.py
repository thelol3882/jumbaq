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

    # ai
    AI_DAILY_LIMIT_REACHED = "ai.daily_limit_reached"
    # The owner switched the model off. The caller uses a built-in story.
    AI_DISABLED = "ai.disabled"
    # The model answered, but with nothing we can use. The caller retries once, then falls back.
    AI_BAD_OUTPUT = "ai.bad_output"
    # The provider is down, slow or busy. The outbox tries again later.
    AI_UNAVAILABLE = "ai.unavailable"

    # billing
    # A case after the free ones needs an active subscription. The web app opens the checkout.
    BILLING_PAYMENT_REQUIRED = "billing.payment_required"
    BILLING_ALREADY_SUBSCRIBED = "billing.already_subscribed"
    BILLING_BAD_SIGNATURE = "billing.bad_signature"
    # No Stripe keys on this server. The rest of the app works.
    BILLING_NOT_CONFIGURED = "billing.not_configured"
    BILLING_UNAVAILABLE = "billing.unavailable"
    # The family has no subscription that gives access, so there is nothing to manage.
    BILLING_NO_SUBSCRIPTION = "billing.no_subscription"

    # cases
    # The family has no case yet: case 1 opens a moment after the setup.
    CASE_NOT_FOUND = "case.not_found"
    # The kids can accuse only after the last episode of the case.
    CASE_NOT_ACCUSING = "case.not_accusing"
    CASE_NOT_SOLVED = "case.not_solved"
    CASE_UNKNOWN_SUSPECT = "case.unknown_suspect"

    # episodes
    EPISODE_NOT_FOUND = "episode.not_found"
    # Still being written, or already played.
    EPISODE_NOT_READY = "episode.not_ready"
    # One episode per evening: this one opens later.
    EPISODE_NOT_AVAILABLE_YET = "episode.not_available_yet"
    EPISODE_ALREADY_SWAPPED = "episode.already_swapped"
    EPISODE_DEMO_MODE_OFF = "episode.demo_mode_off"
    # The step asked for is not the one the evening is in: already done, or not reached yet.
    EPISODE_WRONG_STEP = "episode.wrong_step"
