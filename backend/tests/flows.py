"""Shared steps of the tests."""

import uuid
from typing import Any

from fastapi.testclient import TestClient

from jumbaq.families.deps import FAMILY_COOKIE


def family_body(**changes: Any) -> dict[str, Any]:
    body = {
        "kids": [{"nickname": "Aru", "age": 7}, {"nickname": "Timur", "age": 9}],
        "rooms": ["kitchen", "living room", "bedroom"],
        "objects": ["fridge", "sofa", "bookshelf", "kettle"],
    }
    return body | changes


def create_family(client: TestClient, **changes: Any) -> tuple[uuid.UUID, str]:
    """The id of the new family and its session token from the cookie."""
    response = client.post("/api/v1/families", json=family_body(**changes))
    assert response.status_code == 201, response.text
    return uuid.UUID(response.json()["id"]), response.cookies[FAMILY_COOKIE]
