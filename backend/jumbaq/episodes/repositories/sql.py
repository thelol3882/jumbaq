import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.core.family import FamilyRef
from jumbaq.episodes.domain import CipherLevel, Episode, EpisodeStatus, Payload, Riddle
from jumbaq.episodes.models import EpisodeRow


class SqlEpisodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_if_missing(
        self,
        family: FamilyRef,
        case_id: uuid.UUID,
        case_number: int,
        number: int,
        available_at: datetime,
        created_at: datetime,
    ) -> uuid.UUID | None:
        return await self._session.scalar(
            insert(EpisodeRow)
            .values(
                family_id=family.family_id,
                case_id=case_id,
                case_number=case_number,
                number=number,
                status=EpisodeStatus.REQUESTED,
                available_at=available_at,
                created_at=created_at,
            )
            .on_conflict_do_nothing(index_elements=["case_id", "number"])
            .returning(EpisodeRow.id)
        )

    async def get(
        self, family: FamilyRef, episode_id: uuid.UUID, *, for_update: bool = False
    ) -> Episode | None:
        query = select(EpisodeRow).where(
            EpisodeRow.family_id == family.family_id, EpisodeRow.id == episode_id
        )
        return await self._one(query.with_for_update() if for_update else query)

    async def newest(self, family: FamilyRef) -> Episode | None:
        return await self._one(
            select(EpisodeRow)
            .where(EpisodeRow.family_id == family.family_id)
            .order_by(EpisodeRow.case_number.desc(), EpisodeRow.number.desc())
            .limit(1)
        )

    async def played(self, family: FamilyRef, case_id: uuid.UUID) -> list[Episode]:
        rows = await self._session.scalars(
            select(EpisodeRow)
            .where(
                EpisodeRow.family_id == family.family_id,
                EpisodeRow.case_id == case_id,
                EpisodeRow.status == EpisodeStatus.PLAYED,
            )
            .order_by(EpisodeRow.number)
        )
        return [_episode(row) for row in rows]

    async def set_status(
        self, family: FamilyRef, episode_id: uuid.UUID, status: EpisodeStatus
    ) -> None:
        await self._session.execute(
            update(EpisodeRow)
            .where(EpisodeRow.family_id == family.family_id, EpisodeRow.id == episode_id)
            .values(status=status)
        )

    async def update(self, episode: Episode) -> None:
        await self._session.execute(
            update(EpisodeRow)
            .where(EpisodeRow.family_id == episode.family_id, EpisodeRow.id == episode.id)
            .values(
                status=episode.status,
                payload=asdict(episode.payload) if episode.payload else None,
                answer=episode.answer,
                resolution=episode.resolution,
                available_at=episode.available_at,
                played_at=episode.played_at,
                is_fallback=episode.is_fallback,
                used_fallback_riddle=episode.used_fallback_riddle,
            )
        )

    async def _one(self, query: Select[tuple[EpisodeRow]]) -> Episode | None:
        row = await self._session.scalar(query)
        return _episode(row) if row else None


@dataclass(frozen=True)
class EpisodeSlot:
    """An episode as the case screen lists it."""

    number: int
    id: uuid.UUID
    status: EpisodeStatus
    available_at: datetime | None


class SqlEpisodeLookup:
    """For other modules, on their session: the episodes of a case."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def slots(self, family: FamilyRef, case_id: uuid.UUID) -> list[EpisodeSlot]:
        rows = await self._session.execute(
            select(EpisodeRow.number, EpisodeRow.id, EpisodeRow.status, EpisodeRow.available_at)
            .where(EpisodeRow.family_id == family.family_id, EpisodeRow.case_id == case_id)
            .order_by(EpisodeRow.number)
        )
        return [
            EpisodeSlot(row.number, row.id, EpisodeStatus(row.status), row.available_at)
            for row in rows
        ]


def _episode(row: EpisodeRow) -> Episode:
    return Episode(
        id=row.id,
        family_id=row.family_id,
        case_id=row.case_id,
        case_number=row.case_number,
        number=row.number,
        status=EpisodeStatus(row.status),
        payload=_payload(row.payload) if row.payload else None,
        answer=row.answer,
        resolution=row.resolution,
        available_at=row.available_at,
        played_at=row.played_at,
        is_fallback=row.is_fallback,
        used_fallback_riddle=row.used_fallback_riddle,
    )


def _payload(data: dict[str, Any]) -> Payload:
    return Payload(
        recap=data["recap"],
        read_aloud=tuple(data["read_aloud"]),
        riddle=Riddle(**data["riddle"]),
        hint=data["hint"],
        fallback_riddle=Riddle(**data["fallback_riddle"]),
        resolution_template=data["resolution_template"],
        case_clue=data["case_clue"],
        cliffhanger=data["cliffhanger"],
        clue_suspect_id=data.get("clue_suspect_id"),
        clue_points_at=data.get("clue_points_at"),
        cipher_level=CipherLevel(level) if (level := data.get("cipher_level")) else None,
        cipher_secret=data.get("cipher_secret"),
        cipher_decoys=tuple(data.get("cipher_decoys") or ()),
    )
