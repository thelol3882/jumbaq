"""The owner switch of the model: on, off and the daily cap of all families together."""

from jumbaq.ai import domain
from jumbaq.ai.domain import AiControl, AiStatus
from jumbaq.ai.errors import AiLimitInvalidError
from jumbaq.ai.uow import AiUoWFactory
from jumbaq.core.clock import Clock


class AiControlService:
    def __init__(self, uow: AiUoWFactory, clock: Clock, setting_limit: int) -> None:
        self._uow = uow
        self._clock = clock
        self._setting_limit = setting_limit

    async def status(self) -> AiStatus:
        now = self._clock.now()
        async with self._uow() as uow:
            control = await uow.control.get()
            calls_today = await uow.calls.count_all_between(
                domain.day_start(now), domain.day_end(now)
            )
        return AiStatus(
            enabled=domain.is_enabled(control),
            daily_call_limit=domain.effective_limit(control, self._setting_limit),
            calls_today=calls_today,
            from_table=control is not None,
            limit_from_settings=control is None or control.daily_call_limit is None,
        )

    async def switch(self, enabled: bool) -> AiStatus:
        async with self._uow() as uow:
            current = await uow.control.get()
            limit = current.daily_call_limit if current else None
            await uow.control.save(AiControl(enabled, limit, self._clock.now()))
            await uow.commit()
        return await self.status()

    async def set_daily_limit(self, limit: int) -> AiStatus:
        if limit < 0:
            raise AiLimitInvalidError("the daily limit cannot be negative")
        async with self._uow() as uow:
            current = await uow.control.get()
            enabled = current.enabled if current else True
            await uow.control.save(AiControl(enabled, limit, self._clock.now()))
            await uow.commit()
        return await self.status()
