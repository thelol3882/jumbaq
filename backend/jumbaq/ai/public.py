"""What other modules may use from ai: the StoryWriter facade, its inputs and drafts, and its
errors. The drafts only have the right shape; the caller checks the rules of the game."""

from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.domain import (
    AnswerType,
    CaseDraft,
    CasePlanInput,
    ClueDraft,
    EpisodeDraft,
    EpisodeInput,
    HomeInput,
    KidInput,
    PlayedEpisode,
    RiddleDraft,
    SuspectDraft,
)
from jumbaq.ai.errors import AiBadOutputError, AiDailyLimitError, AiUnavailableError
from jumbaq.ai.prompts import ANSWER_SLOT, EPISODES_PER_CASE, SUSPECTS_PER_CASE
from jumbaq.ai.providers.base import Provider
from jumbaq.ai.providers.claude import ClaudeProvider
from jumbaq.ai.providers.stub import StubProvider
from jumbaq.ai.services.writer import StoryWriter
from jumbaq.ai.uow import AiUoW
from jumbaq.core.clock import Clock
from jumbaq.core.config import Settings


def build_provider(settings: Settings) -> Provider:
    if settings.ai_provider == "claude":
        assert settings.ai_api_key is not None  # Settings checks it
        return ClaudeProvider(
            settings.ai_api_key.get_secret_value(), settings.ai_model, settings.ai_timeout_seconds
        )
    return StubProvider()


def build_story_writer(
    sessionmaker: async_sessionmaker[AsyncSession],
    settings: Settings,
    clock: Clock,
    provider: Provider | None = None,
) -> StoryWriter:
    """For the worker. Tests pass their own provider."""
    return StoryWriter(
        partial(AiUoW, sessionmaker),
        provider or build_provider(settings),
        clock,
        settings.ai_daily_calls_per_family,
    )


__all__ = [
    "ANSWER_SLOT",
    "EPISODES_PER_CASE",
    "SUSPECTS_PER_CASE",
    "AiBadOutputError",
    "AiDailyLimitError",
    "AiUnavailableError",
    "AnswerType",
    "CaseDraft",
    "CasePlanInput",
    "ClueDraft",
    "EpisodeDraft",
    "EpisodeInput",
    "HomeInput",
    "KidInput",
    "PlayedEpisode",
    "Provider",
    "RiddleDraft",
    "StoryWriter",
    "SuspectDraft",
    "build_story_writer",
]
