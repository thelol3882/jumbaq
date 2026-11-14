from jumbaq.core.error_codes import ErrorCode
from jumbaq.core.errors import FieldError, NotAuthenticatedError


class NoFamilySessionError(NotAuthenticatedError):
    """The same answer for a missing cookie and an unknown one."""

    code = ErrorCode.FAMILY_NO_SESSION


class KidNicknameRepeatedError(FieldError):
    def __init__(self) -> None:
        super().__init__("kids", ErrorCode.FAMILY_KID_NICKNAME_REPEATED)
