import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Nickname = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class KidIn(BaseModel):
    nickname: Nickname
    age: Annotated[int, Field(ge=3, le=14)]


class FamilyCreate(BaseModel):
    kids: Annotated[list[KidIn], Field(min_length=1, max_length=6)]
    rooms: Annotated[list[Label], Field(min_length=1, max_length=20)]
    # The household objects the parent ticked. Riddles point only at these.
    objects: Annotated[list[Label], Field(min_length=3, max_length=100)]

    @field_validator("rooms", "objects")
    @classmethod
    def without_repeats(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))


class KidOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nickname: str
    age: int


class FamilyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kids: list[KidOut]
    rooms: list[str]
    objects: list[str]
    created_at: datetime
