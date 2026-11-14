"""The OpenRouter provider against a mock transport: no network, no key."""

import json
from typing import Any

import httpx
import pytest

from jumbaq.ai.errors import AiBadOutputError, AiUnavailableError
from jumbaq.ai.prompts import CASE_PLAN_SCHEMA, Prompt
from jumbaq.ai.providers.openrouter import OpenRouterProvider
from jumbaq.ai.public import build_provider
from jumbaq.core.config import Settings

PROMPT = Prompt("Plan a case.", "<family_data>{}</family_data>")
MODEL = "google/gemma-4-31b-it:free"


def answer(content: str, finish_reason: str = "stop") -> dict[str, Any]:
    return {
        "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 300, "completion_tokens": 120},
    }


def provider(handler: Any) -> OpenRouterProvider:
    return OpenRouterProvider("or-test-key", MODEL, 5, transport=httpx.MockTransport(handler))


def replying(status: int, body: dict[str, Any]) -> OpenRouterProvider:
    return provider(lambda request: httpx.Response(status, json=body))


async def test_the_request_asks_for_json_of_the_schema() -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json=answer('{"title": "x"}'))

    reply = await provider(handler).complete_json(PROMPT, CASE_PLAN_SCHEMA)

    assert (reply.data, reply.input_tokens, reply.output_tokens) == ({"title": "x"}, 300, 120)
    body = json.loads(sent[0].content)
    assert sent[0].headers["Authorization"] == "Bearer or-test-key"
    assert body["model"] == MODEL
    assert body["response_format"]["json_schema"]["schema"] == CASE_PLAN_SCHEMA
    # For models that ignore response_format.
    assert json.dumps(CASE_PLAN_SCHEMA) in body["messages"][0]["content"]
    assert body["messages"][1]["content"] == PROMPT.user


async def test_json_in_a_code_block_is_read() -> None:
    reply = await replying(200, answer('```json\n{"title": "x"}\n```')).complete_json(PROMPT, {})
    assert reply.data == {"title": "x"}


@pytest.mark.parametrize(
    "body",
    [answer("{}", finish_reason="length"), answer("Here is your case!"), answer("[1]"),
     answer("")],
)  # fmt: skip
async def test_unusable_answers_are_bad_output(body: dict[str, Any]) -> None:
    with pytest.raises(AiBadOutputError):
        await replying(200, body).complete_json(PROMPT, {})


async def test_a_rejected_request_is_bad_output() -> None:
    with pytest.raises(AiBadOutputError):
        await replying(400, {"error": {"code": 400}}).complete_json(PROMPT, {})


@pytest.mark.parametrize("status", [429, 500, 502, 401, 402])
async def test_errors_worth_a_retry_are_unavailable(status: int) -> None:
    with pytest.raises(AiUnavailableError):
        await replying(status, {"error": {"code": status}}).complete_json(PROMPT, {})


async def test_an_error_inside_a_200_is_unavailable() -> None:
    with pytest.raises(AiUnavailableError):
        await replying(200, {"error": {"code": 429, "message": "busy"}}).complete_json(PROMPT, {})


async def test_network_errors_are_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("slow", request=request)

    with pytest.raises(AiUnavailableError):
        await provider(handler).complete_json(PROMPT, {})


def test_settings_choose_openrouter() -> None:
    settings = Settings(
        database_url="x", redis_url="y", ai_provider="openrouter", ai_api_key="or-key"
    )
    chosen = build_provider(settings)
    assert isinstance(chosen, OpenRouterProvider)
    assert chosen.model == MODEL
