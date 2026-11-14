"""OpenRouter, for laptops: its ":free" models cost nothing, so the team can try real stories
without a paid key. Free models are slower, rate-limited and change often, so the server uses
Claude."""

import json
import logging
import re
from typing import Any

import httpx

from jumbaq.ai.errors import AiBadOutputError, AiUnavailableError
from jumbaq.ai.prompts import Prompt
from jumbaq.ai.providers.base import Reply

logger = logging.getLogger(__name__)

URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TOKENS = 16000
# Some free models ignore response_format and wrap the JSON in a ```json block.
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class OpenRouterProvider:
    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._timeout = timeout_seconds
        # Tests pass a mock transport instead of the network.
        self._transport = transport

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        # The schema also goes into the prompt, for models that do not support response_format.
        system = (
            f"{prompt.system}\n\nAnswer with one JSON object only, no other text. It must match "
            f"this JSON schema:\n{json.dumps(schema)}"
        )
        body = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt.user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "answer", "strict": True, "schema": schema},
            },
        }
        try:
            client = httpx.AsyncClient(timeout=self._timeout, transport=self._transport)
            async with client:
                response = await client.post(
                    URL, json=body, headers={"Authorization": f"Bearer {self._api_key}"}
                )
        except httpx.HTTPError as error:
            raise AiUnavailableError(type(error).__name__) from error

        if response.status_code == 400:
            raise AiBadOutputError("OpenRouter rejected the request")
        if response.status_code != 200:
            # 429 is the usual one on free models. 401, 402 and 5xx: retrying may help or
            # ends in failed_at, where someone sees it.
            raise AiUnavailableError(f"OpenRouter answered {response.status_code}")
        return _reply(response.json())


def _reply(answer: dict[str, Any]) -> Reply:
    if "error" in answer:
        # OpenRouter can answer 200 with the error of the model's provider inside.
        raise AiUnavailableError(f"OpenRouter error {answer['error'].get('code')}")
    choice = (answer.get("choices") or [{}])[0]
    if choice.get("finish_reason") not in ("stop", None):
        raise AiBadOutputError(f"the model stopped with {choice.get('finish_reason')}")
    data = _json_object((choice.get("message") or {}).get("content") or "")
    usage = answer.get("usage") or {}
    return Reply(data, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))


def _json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise AiBadOutputError("the answer is not JSON") from error
    if not isinstance(data, dict):
        raise AiBadOutputError("the answer is not a JSON object")
    return data
