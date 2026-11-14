"""A detective case of 5 episodes. Case 1 is free."""

from enum import StrEnum

FIRST_CASE = 1


class CaseStatus(StrEnum):
    """planning -> active -> accusing -> solved, and planning -> failed."""

    PLANNING = "planning"
    ACTIVE = "active"
    ACCUSING = "accusing"
    SOLVED = "solved"
    FAILED = "failed"


class Rank(StrEnum):
    """By the number of accusations it took. The values are translation keys of the web app,
    so a rename happens here and in its texts only."""

    FIRST_TRY = "chief_detective"
    SECOND_TRY = "detective"
    LATER = "junior_detective"
