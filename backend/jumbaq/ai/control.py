"""The owner switch of the model, from the server:

    python -m jumbaq.ai.control status | on | off | limit <n>

An entry point like a router: it builds the service the way the app does, calls one method and
prints the result. Exit code 0 on success, 2 on bad input.
"""

import argparse
import asyncio
import sys
from collections.abc import Sequence
from functools import partial
from typing import TextIO

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.domain import AiStatus
from jumbaq.ai.errors import AiLimitInvalidError
from jumbaq.ai.services.control import AiControlService
from jumbaq.ai.uow import AiUoW
from jumbaq.core.clock import Clock, SystemClock
from jumbaq.core.config import Settings
from jumbaq.core.db import create_engine, create_sessionmaker

BAD_INPUT = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m jumbaq.ai.control")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="show the switch, the daily limit and today's calls")
    commands.add_parser("on", help="let the model write stories")
    commands.add_parser("off", help="play built-in stories only")
    limit = commands.add_parser("limit", help="set the daily limit of calls for all families")
    limit.add_argument("n", type=int)
    return parser


def _show(status: AiStatus, settings: Settings) -> str:
    where = "table" if status.from_table else "settings"
    limit_where = "settings" if status.limit_from_settings else "table"
    return "\n".join(
        [
            f"enabled: {'yes' if status.enabled else 'no'} (from {where})",
            f"daily limit: {status.daily_call_limit} (from {limit_where})",
            f"calls today: {status.calls_today}",
            f"provider: {settings.ai_provider}",
        ]
    )


async def run(
    argv: Sequence[str],
    sessionmaker: async_sessionmaker[AsyncSession],
    settings: Settings,
    clock: Clock,
    out: TextIO,
) -> int:
    args = _parser().parse_args(argv)
    service = AiControlService(partial(AiUoW, sessionmaker), clock, settings.ai_daily_call_limit)
    try:
        match args.command:
            case "on":
                status = await service.switch(True)
            case "off":
                status = await service.switch(False)
            case "limit":
                status = await service.set_daily_limit(args.n)
            case _:
                status = await service.status()
    except AiLimitInvalidError as error:
        print(error, file=sys.stderr)
        return BAD_INPUT
    print(_show(status, settings), file=out)
    return 0


async def _main(argv: Sequence[str]) -> int:
    settings = Settings()
    engine = create_engine(settings.database_url)
    try:
        return await run(argv, create_sessionmaker(engine), settings, SystemClock(), sys.stdout)
    finally:
        await engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    return asyncio.run(_main(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    sys.exit(main())
