from dataclasses import dataclass
from typing import Any, Protocol

from jumbaq.ai.prompts import Prompt


@dataclass(frozen=True)
class Reply:
    data: dict[str, Any]
    input_tokens: int
    output_tokens: int


class Provider(Protocol):
    """A model that answers a prompt with a JSON object of the given schema.

    Raises AiUnavailableError when trying later may help, and AiBadOutputError when it will not.
    """

    name: str
    model: str

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply: ...
