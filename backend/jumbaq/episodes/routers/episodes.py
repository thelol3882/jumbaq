"""The episodes of a family: one evening each, with a riddle about the home."""

import uuid

from fastapi import APIRouter

from jumbaq.episodes.deps import EpisodeServiceDep
from jumbaq.episodes.schemas import AnswerIn, EpisodeOut
from jumbaq.families.deps import FamilyDep

router = APIRouter(tags=["episodes"])


@router.get("/episodes/current")
async def get_current_episode(family: FamilyDep, episodes: EpisodeServiceDep) -> EpisodeOut:
    """The episode to show now. `content` is null while it is written or not yet available.
    404 `episode.not_found` while the case is planned."""
    return EpisodeOut.model_validate(await episodes.current(family))


@router.get("/episodes/{episode_id}")
async def get_episode(
    episode_id: uuid.UUID, family: FamilyDep, episodes: EpisodeServiceDep
) -> EpisodeOut:
    """Another family's episode gives 404 `episode.not_found`."""
    return EpisodeOut.model_validate(await episodes.get(family, episode_id))


@router.post("/episodes/{episode_id}/answer")
async def answer_episode(
    episode_id: uuid.UUID, body: AnswerIn, family: FamilyDep, episodes: EpisodeServiceDep
) -> EpisodeOut:
    """Any answer fits the story. Only for a ready episode (409 `episode.not_ready`) that is
    available (409 `episode.not_available_yet`). The result is in `content.result`."""
    return EpisodeOut.model_validate(await episodes.answer(family, episode_id, body.answer))


@router.post("/episodes/{episode_id}/swap")
async def swap_riddle(
    episode_id: uuid.UUID, family: FamilyDep, episodes: EpisodeServiceDep
) -> EpisodeOut:
    """Switches to the second riddle when the object is not at hand. Once per episode
    (409 `episode.already_swapped`)."""
    return EpisodeOut.model_validate(await episodes.swap(family, episode_id))


@router.post("/episodes/{episode_id}/open-now")
async def open_episode_now(
    episode_id: uuid.UUID, family: FamilyDep, episodes: EpisodeServiceDep
) -> EpisodeOut:
    """Opens a waiting episode at once, so the jury can play a case in minutes. Only in demo
    mode (403 `episode.demo_mode_off`)."""
    return EpisodeOut.model_validate(await episodes.open_now(family, episode_id))
