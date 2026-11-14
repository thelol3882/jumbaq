from jumbaq.core.error_codes import ErrorCode
from jumbaq.core.errors import ConflictError, FieldError, NotFoundError


class CaseNotFoundError(NotFoundError):
    """Also for another family's case: the same answer as for one that does not exist."""

    code = ErrorCode.CASE_NOT_FOUND


class CaseNotAccusingError(ConflictError):
    code = ErrorCode.CASE_NOT_ACCUSING


class CaseNotSolvedError(ConflictError):
    code = ErrorCode.CASE_NOT_SOLVED


class UnknownSuspectError(FieldError):
    def __init__(self) -> None:
        super().__init__("suspect_id", ErrorCode.CASE_UNKNOWN_SUSPECT)
