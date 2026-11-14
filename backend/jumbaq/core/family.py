"""Who acts, as services see it. `families.deps` makes it from the session cookie, the worker
makes it from an event, so services do not depend on HTTP."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class FamilyRef:
    family_id: uuid.UUID
