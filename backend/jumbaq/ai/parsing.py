"""Turns the model's JSON into drafts. Checks the shape only, not the rules of the game."""

from typing import Any

from pydantic import TypeAdapter, ValidationError

from jumbaq.ai.domain import CaseDraft, EpisodeDraft
from jumbaq.ai.errors import AiBadOutputError

_CASE = TypeAdapter(CaseDraft)
_EPISODE = TypeAdapter(EpisodeDraft)


def case_draft(data: dict[str, Any]) -> CaseDraft:
    try:
        return _CASE.validate_python(data, strict=False)
    except ValidationError as error:
        raise AiBadOutputError("case plan of the wrong shape") from error


def episode_draft(data: dict[str, Any]) -> EpisodeDraft:
    try:
        return _EPISODE.validate_python(data, strict=False)
    except ValidationError as error:
        raise AiBadOutputError("episode of the wrong shape") from error
