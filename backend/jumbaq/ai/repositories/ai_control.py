from typing import Protocol

from jumbaq.ai.domain import AiControl


class AiControlRepository(Protocol):
    async def get(self) -> AiControl | None: ...

    async def save(self, control: AiControl) -> None:
        """Inserts the one row or replaces it."""
        ...
