"""A family: the kids who play, the rooms of the home and the objects the riddles may point at."""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime

from jumbaq.families.errors import KidNicknameRepeatedError


@dataclass(frozen=True)
class NewKid:
    nickname: str
    age: int


@dataclass(frozen=True)
class Kid:
    id: uuid.UUID
    nickname: str
    age: int


@dataclass(frozen=True)
class NewFamily:
    rooms: tuple[str, ...]
    objects: tuple[str, ...]
    kids: tuple[NewKid, ...]
    session_token_hash: str
    created_at: datetime


@dataclass(frozen=True)
class Family:
    id: uuid.UUID
    rooms: tuple[str, ...]
    objects: tuple[str, ...]
    kids: tuple[Kid, ...]
    created_at: datetime


def check_kids(kids: tuple[NewKid, ...]) -> None:
    # The parent reads the nicknames aloud, so two kids must not sound the same.
    nicknames = [kid.nickname.casefold() for kid in kids]
    if len(set(nicknames)) != len(nicknames):
        raise KidNicknameRepeatedError()


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Only this is stored, so a copy of the database opens no session."""
    return hashlib.sha256(token.encode()).hexdigest()
