from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.ai.repositories.ai_control import AiControlRepository
from jumbaq.ai.repositories.llm_calls import LlmCallRepository
from jumbaq.ai.repositories.sql import SqlAiControlRepository, SqlLlmCallRepository
from jumbaq.core.db import UnitOfWork


class AiUoW(UnitOfWork):
    calls: LlmCallRepository
    control: AiControlRepository

    def _attach(self, session: AsyncSession) -> None:
        self.calls = SqlLlmCallRepository(session)
        self.control = SqlAiControlRepository(session)


AiUoWFactory = Callable[[], AiUoW]
