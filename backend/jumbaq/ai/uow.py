from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.ai.repositories.llm_calls import LlmCallRepository
from jumbaq.ai.repositories.sql import SqlLlmCallRepository
from jumbaq.core.db import UnitOfWork


class AiUoW(UnitOfWork):
    calls: LlmCallRepository

    def _attach(self, session: AsyncSession) -> None:
        self.calls = SqlLlmCallRepository(session)


AiUoWFactory = Callable[[], AiUoW]
