"""What the services of episodes need from storage."""

import uuid
from datetime import datetime
from typing import Protocol

from jumbaq.core.family import FamilyRef
from jumbaq.episodes.domain import Episode, EpisodeStatus


class EpisodeRepository(Protocol):
    async def add_if_missing(
        self,
        family: FamilyRef,
        case_id: uuid.UUID,
        case_number: int,
        number: int,
        available_at: datetime,
        created_at: datetime,
    ) -> uuid.UUID | None:
        """The id of the new episode, requested. None when the case already has this number."""
        ...

    async def get(
        self, family: FamilyRef, episode_id: uuid.UUID, *, for_update: bool = False
    ) -> Episode | None: ...

    async def newest(self, family: FamilyRef) -> Episode | None: ...

    async def played(self, family: FamilyRef, case_id: uuid.UUID) -> list[Episode]:
        """The played episodes of the case, in order."""
        ...

    async def set_status(
        self, family: FamilyRef, episode_id: uuid.UUID, status: EpisodeStatus
    ) -> None: ...

    async def update(self, episode: Episode) -> None:
        """Saves what can change: status, payload, answer, the steps, times and the swap."""
        ...
