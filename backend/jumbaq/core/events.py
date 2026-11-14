"""Events that modules publish.

    @dataclass(frozen=True)
    class FamilyCreated(Event):
        topic: ClassVar[str] = "families.created"

An event carries only ids: never a secret and never personal data, because outbox rows stay
in the database and its backups. The handler loads what it needs.
"""

import uuid
from dataclasses import dataclass, fields
from typing import Any, ClassVar, Self, get_type_hints

_ALLOWED = (uuid.UUID, str, int, bool, type(None))


@dataclass(frozen=True)
class Event:
    topic: ClassVar[str]
    family_id: uuid.UUID

    def to_payload(self) -> dict[str, Any]:
        payload = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, _ALLOWED):
                raise TypeError(f"{self.topic}.{field.name} must be an id, text, a number or None")
            payload[field.name] = str(value) if isinstance(value, uuid.UUID) else value
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        hints = get_type_hints(cls)
        values = {
            field.name: uuid.UUID(payload[field.name])
            if hints[field.name] in (uuid.UUID, uuid.UUID | None) and payload[field.name]
            else payload[field.name]
            for field in fields(cls)
        }
        return cls(**values)
