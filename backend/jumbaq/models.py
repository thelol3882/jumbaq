"""Imports the models of every module, so `Base.metadata` has all tables.

Alembic and the schema tests use it. The app itself does not need it.
"""

from jumbaq.ai import models as ai_models
from jumbaq.billing import models as billing_models
from jumbaq.cases import models as cases_models
from jumbaq.core import outbox as outbox_models
from jumbaq.core.db import Base
from jumbaq.episodes import models as episodes_models
from jumbaq.families import models as families_models

__all__ = [
    "Base",
    "ai_models",
    "billing_models",
    "cases_models",
    "episodes_models",
    "families_models",
    "outbox_models",
]
