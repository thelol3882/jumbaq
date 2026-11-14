from collections.abc import Callable

from jumbaq.core.db import UnitOfWork


class EpisodesUoW(UnitOfWork):
    """The repositories come with the episode table."""


EpisodesUoWFactory = Callable[[], EpisodesUoW]
