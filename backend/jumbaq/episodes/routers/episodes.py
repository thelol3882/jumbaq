"""The episodes of a family: one evening each, with a riddle about the home."""

import uuid

from fastapi import APIRouter

from jumbaq.episodes.deps import EpisodeServiceDep
from jumbaq.episodes.schemas import AnswerIn, DecodeIn, EpisodeOut, StrikeIn
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
    """Step 1 of 3. Any answer fits the story. Only for a ready episode (409
    `episode.not_ready`) that is available (409 `episode.not_available_yet`). A second answer
    gives 409 `episode.wrong_step`. The cipher to decode is then in `content.decode`; an
    episode without a cipher is played here and its result is in `content.result`."""
    return EpisodeOut.model_validate(await episodes.answer(family, episode_id, body.answer))


@router.post("/episodes/{episode_id}/decode")
async def decode_episode(
    episode_id: uuid.UUID, body: DecodeIn, family: FamilyDep, episodes: EpisodeServiceDep
) -> EpisodeOut:
    """Step 2 of 3: the word the kids picked, or null for the count level. A wrong pick is not
    an error: the step stays and `attempts` grows. After the second wrong one the word is
    given away and the step moves on. Outside this step: 409 `episode.wrong_step`."""
    return EpisodeOut.model_validate(await episodes.decode(family, episode_id, body.word))


@router.post("/episodes/{episode_id}/strike")
async def strike_episode(
    episode_id: uuid.UUID, body: StrikeIn, family: FamilyDep, episodes: EpisodeServiceDep
) -> EpisodeOut:
    """Step 3 of 3: the suspect the clue is about. A wrong one is not an error: `attempts`
    grows. The right one, or the second wrong one, ends the evening as played with the result
    in `content.result`. Outside this step: 409 `episode.wrong_step`."""
    return EpisodeOut.model_validate(await episodes.strike(family, episode_id, body.suspect_id))


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
