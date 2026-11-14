"""Asks the model for a case plan or an episode, within the daily cap of the family and the
daily cap of all families together."""

import time
from collections.abc import Callable
from typing import Any

from jumbaq.ai import domain, parsing, prompts
from jumbaq.ai.domain import (
    CallOutcome,
    CaseDraft,
    CasePlanInput,
    EpisodeDraft,
    EpisodeInput,
    LlmCall,
    TaskKind,
)
from jumbaq.ai.errors import AiBadOutputError, AiDailyLimitError, AiUnavailableError
from jumbaq.ai.prompts import Prompt
from jumbaq.ai.providers.base import Provider
from jumbaq.ai.uow import AiUoWFactory
from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef


class StoryWriter:
    def __init__(
        self,
        uow: AiUoWFactory,
        provider: Provider,
        clock: Clock,
        daily_limit: int,
        global_daily_limit: int,
    ) -> None:
        self._uow = uow
        self._provider = provider
        self._clock = clock
        self._daily_limit = daily_limit
        self._global_daily_limit = global_daily_limit

    async def plan_case(self, family: FamilyRef, task: CasePlanInput) -> CaseDraft:
        return await self._call(
            family,
            TaskKind.CASE_PLAN,
            prompts.case_plan_prompt(task),
            prompts.CASE_PLAN_SCHEMA,
            parsing.case_draft,
        )

    async def write_episode(self, family: FamilyRef, task: EpisodeInput) -> EpisodeDraft:
        return await self._call(
            family,
            TaskKind.EPISODE,
            prompts.episode_prompt(task),
            prompts.EPISODE_SCHEMA,
            parsing.episode_draft,
        )

    async def _call[T](
        self,
        family: FamilyRef,
        kind: TaskKind,
        prompt: Prompt,
        schema: dict[str, Any],
        parse: Callable[[dict[str, Any]], T],
    ) -> T:
        await self._check_limit(family)
        # The call runs outside any transaction, so a slow model holds no connection.
        # Two calls at the same moment can both pass the cap; it limits cost, not access.
        started = time.perf_counter()
        input_tokens = output_tokens = 0
        try:
            reply = await self._provider.complete_json(prompt, schema)
            input_tokens, output_tokens = reply.input_tokens, reply.output_tokens
            result = parse(reply.data)
        except AiBadOutputError:
            # A reply of the wrong shape still cost its tokens.
            await self._record(
                family, kind, CallOutcome.BAD_OUTPUT, started, input_tokens, output_tokens
            )
            raise
        except AiUnavailableError:
            await self._record(family, kind, CallOutcome.UNAVAILABLE, started, 0, 0)
            raise
        await self._record(family, kind, CallOutcome.OK, started, input_tokens, output_tokens)
        return result

    async def _check_limit(self, family: FamilyRef) -> None:
        now = self._clock.now()
        start, end = domain.day_start(now), domain.day_end(now)
        async with self._uow() as uow:
            calls_today = await uow.calls.count_between(family, start, end)
            all_calls_today = await uow.calls.count_all_between(start, end)
        if domain.limit_reached(calls_today, self._daily_limit) or domain.limit_reached(
            all_calls_today, self._global_daily_limit
        ):
            raise AiDailyLimitError()

    async def _record(
        self,
        family: FamilyRef,
        kind: TaskKind,
        outcome: CallOutcome,
        started: float,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        call = LlmCall(
            family_id=family.family_id,
            kind=kind,
            provider=self._provider.name,
            model=self._provider.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            # A duration, not a time anyone sees, so it does not come from the Clock.
            duration_ms=round((time.perf_counter() - started) * 1000),
            outcome=outcome,
            created_at=self._clock.now(),
        )
        async with self._uow() as uow:
            await uow.calls.add(call)
            await uow.commit()
