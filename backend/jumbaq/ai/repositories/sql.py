import uuid
from datetime import datetime

from sqlalchemy import func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.ai.domain import AiControl, CallOutcome, LlmCall
from jumbaq.ai.models import AiControlRow, LlmCallRow
from jumbaq.core.family import FamilyRef


class SqlLlmCallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, call: LlmCall) -> uuid.UUID:
        call_id = await self._session.scalar(
            insert(LlmCallRow)
            .values(
                family_id=call.family_id,
                kind=call.kind,
                provider=call.provider,
                model=call.model,
                input_tokens=call.input_tokens,
                output_tokens=call.output_tokens,
                duration_ms=call.duration_ms,
                outcome=call.outcome,
                created_at=call.created_at,
            )
            .returning(LlmCallRow.id)
        )
        assert call_id is not None
        return call_id

    async def mark_refused(self, family: FamilyRef, call_id: uuid.UUID) -> None:
        await self._session.execute(
            update(LlmCallRow)
            .where(
                LlmCallRow.family_id == family.family_id,
                LlmCallRow.id == call_id,
                LlmCallRow.outcome == CallOutcome.OK,
            )
            .values(outcome=CallOutcome.REFUSED)
        )

    async def count_all_between(self, start: datetime, end: datetime) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(LlmCallRow)
            .where(LlmCallRow.created_at >= start, LlmCallRow.created_at < end)
        )
        return count or 0

    async def count_between(self, family: FamilyRef, start: datetime, end: datetime) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(LlmCallRow)
            .where(
                LlmCallRow.family_id == family.family_id,
                LlmCallRow.created_at >= start,
                LlmCallRow.created_at < end,
            )
        )
        return count or 0


class SqlAiControlRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> AiControl | None:
        row = await self._session.get(AiControlRow, 1)
        if row is None:
            return None
        return AiControl(row.enabled, row.daily_call_limit, row.updated_at)

    async def save(self, control: AiControl) -> None:
        values = {
            "enabled": control.enabled,
            "daily_call_limit": control.daily_call_limit,
            "updated_at": control.updated_at,
        }
        await self._session.execute(
            pg_insert(AiControlRow)
            .values(id=1, **values)
            .on_conflict_do_update(index_elements=[AiControlRow.id], set_=values)
        )
