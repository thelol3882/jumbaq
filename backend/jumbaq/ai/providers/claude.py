"""Claude through the official Anthropic SDK, with structured outputs so the answer is JSON of
our schema."""

import json
import logging
from typing import Any

import anthropic

from jumbaq.ai.errors import AiBadOutputError, AiUnavailableError
from jumbaq.ai.prompts import Prompt
from jumbaq.ai.providers.base import Reply

logger = logging.getLogger(__name__)

# Long enough for an episode with its thinking. Hitting it gives a cut answer.
MAX_TOKENS = 16000
# If a safety check declines a request, the API runs it again on another model in the same
# call. A gentle kids' story should never need it, but a false refusal must not break an evening.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MODELS_WITH_FALLBACKS = frozenset(
    {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-2"}
)


class ClaudeProvider:
    name = "claude"

    def __init__(self, api_key: str, model: str, timeout_seconds: float) -> None:
        self.model = model
        # One quick retry in the SDK. Longer waits belong to the outbox, which retries the event.
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key, timeout=timeout_seconds, max_retries=1
        )

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        fallbacks: dict[str, Any] = (
            {"betas": [FALLBACK_BETA], "fallbacks": "default"}
            if self.model in MODELS_WITH_FALLBACKS
            else {}
        )
        try:
            response = await self._client.beta.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=prompt.system,
                messages=[{"role": "user", "content": prompt.user}],
                output_config={
                    "effort": "medium",
                    "format": {"type": "json_schema", "schema": schema},
                },
                **fallbacks,
            )
        except (anthropic.APIConnectionError, anthropic.RateLimitError) as error:
            # APIConnectionError also covers timeouts.
            raise AiUnavailableError(type(error).__name__) from error
        except anthropic.InternalServerError as error:
            raise AiUnavailableError(f"provider error {error.status_code}") from error
        except anthropic.BadRequestError as error:
            # Our request is wrong, so sending it again later gives the same answer.
            raise AiBadOutputError("the provider rejected the request") from error
        except anthropic.APIStatusError as error:
            # A wrong key or model. The outbox retries and the row ends in failed_at, where
            # someone sees it, instead of every episode quietly using its fallback.
            raise AiUnavailableError(f"provider error {error.status_code}") from error

        if response.stop_reason != "end_turn":
            logger.warning("model stopped with %s, request %s", response.stop_reason, response.id)
            raise AiBadOutputError(f"the model stopped with {response.stop_reason}")
        text = next((block.text for block in response.content if block.type == "text"), None)
        try:
            data = json.loads(text) if text is not None else None
        except json.JSONDecodeError:
            data = None
        if not isinstance(data, dict):
            raise AiBadOutputError("the answer is not a JSON object")
        return Reply(data, response.usage.input_tokens, response.usage.output_tokens)
