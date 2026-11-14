"""The one list of which handler runs for which event.

Apart from main.py, which reads the Redis url at import time for arq, so that tests and
scripts can build the handlers without the worker's settings.
"""

from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.public import StoryWriter
from jumbaq.billing.public import SubscriptionActivated
from jumbaq.cases.handlers import CasesHandlers
from jumbaq.cases.public import CaseOpened, CasePlanned, CaseSolved
from jumbaq.cases.services.planning import CasePlanning
from jumbaq.cases.services.progress import CaseProgress
from jumbaq.cases.uow import CasesUoW
from jumbaq.core.clock import Clock
from jumbaq.core.events import Event
from jumbaq.core.outbox import Handler
from jumbaq.episodes.handlers import EpisodesHandlers
from jumbaq.episodes.public import EpisodePlayed, EpisodeRequested
from jumbaq.episodes.services.writing import EpisodeWriting
from jumbaq.episodes.uow import EpisodesUoW
from jumbaq.families.public import FamilyCreated


def build_handlers(
    sessionmaker: async_sessionmaker[AsyncSession], writer: StoryWriter, clock: Clock
) -> dict[type[Event], list[Handler]]:
    """Which handlers run for which event. Handlers come from the `handlers.py` of each module.

    The writer is built once in `startup` and shared, like the engine.
    """
    cases_uow = partial(CasesUoW, sessionmaker)
    cases = CasesHandlers(CasePlanning(cases_uow, writer), CaseProgress(cases_uow))
    episodes = EpisodesHandlers(EpisodeWriting(partial(EpisodesUoW, sessionmaker), writer, clock))
    return {
        FamilyCreated: [cases.family_created],
        CaseOpened: [cases.case_opened],
        CasePlanned: [episodes.case_planned],
        EpisodeRequested: [episodes.episode_requested],
        EpisodePlayed: [cases.episode_played],
        # Registered without handlers, so their rows are marked processed and do not fail.
        CaseSolved: [],
        SubscriptionActivated: [],
    }
