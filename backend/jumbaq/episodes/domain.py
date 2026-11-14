"""An episode of a case: one evening of reading aloud with a riddle about the home."""

from enum import StrEnum


class EpisodeStatus(StrEnum):
    REQUESTED = "requested"
    GENERATING = "generating"
    READY = "ready"
    PLAYED = "played"
    FAILED = "failed"
