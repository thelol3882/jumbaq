"""Imports the models of every module, so `Base.metadata` has all tables.

Alembic and the schema tests use it. The app itself does not need it.
"""

from jumbaq.core import outbox as outbox_models
from jumbaq.core.db import Base

__all__ = ["Base", "outbox_models"]
