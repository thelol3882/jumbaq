from datetime import datetime

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.ai.domain import LlmCall
from jumbaq.ai.models import LlmCallRow
from jumbaq.core.family import FamilyRef


class SqlLlmCallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, call: LlmCall) -> None:
        await self._session.execute(
            insert(LlmCallRow).values(
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
        )

    async def count_all_since(self, since: datetime) -> int:
        count = await self._session.scalar(
            select(func.count()).select_from(LlmCallRow).where(LlmCallRow.created_at >= since)
        )
        return count or 0

    async def count_since(self, family: FamilyRef, since: datetime) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(LlmCallRow)
            .where(LlmCallRow.family_id == family.family_id, LlmCallRow.created_at >= since)
        )
        return count or 0
