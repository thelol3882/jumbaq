from jumbaq.core.error_codes import ErrorCode
from jumbaq.core.errors import ConflictError, ForbiddenError, NotFoundError


class EpisodeNotFoundError(NotFoundError):
    """Also for another family's episode: the same answer as for one that does not exist."""

    code = ErrorCode.EPISODE_NOT_FOUND


class EpisodeNotReadyError(ConflictError):
    """Still being written."""

    code = ErrorCode.EPISODE_NOT_READY


class EpisodeNotAvailableYetError(ConflictError):
    code = ErrorCode.EPISODE_NOT_AVAILABLE_YET


class RiddleAlreadySwappedError(ConflictError):
    code = ErrorCode.EPISODE_ALREADY_SWAPPED


class DemoModeOffError(ForbiddenError):
    code = ErrorCode.EPISODE_DEMO_MODE_OFF


class EpisodeWrongStepError(ConflictError):
    code = ErrorCode.EPISODE_WRONG_STEP
