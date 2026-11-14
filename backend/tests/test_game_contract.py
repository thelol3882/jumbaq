"""Every endpoint of the game exists and acts only for a family. The web app's types come from
these routes, so a lost route must fail here."""

import uuid

import pytest
from fastapi.testclient import TestClient

from jumbaq.families.deps import FAMILY_COOKIE

pytestmark = pytest.mark.integration

ANY = uuid.uuid4()
ENDPOINTS = [
    ("GET", "/api/v1/cases/current", None),
    ("POST", "/api/v1/cases", None),
    ("POST", f"/api/v1/cases/{ANY}/accuse", {"suspect_id": "s1"}),
    ("GET", f"/api/v1/cases/{ANY}/certificate", None),
    ("GET", "/api/v1/episodes/current", None),
    ("GET", f"/api/v1/episodes/{ANY}", None),
    ("POST", f"/api/v1/episodes/{ANY}/answer", {"answer": "7"}),
    ("POST", f"/api/v1/episodes/{ANY}/swap", None),
    ("POST", f"/api/v1/episodes/{ANY}/open-now", None),
]


@pytest.mark.parametrize(("method", "path", "body"), ENDPOINTS)
def test_the_game_needs_a_family(
    live_client: TestClient, method: str, path: str, body: dict[str, str] | None
) -> None:
    live_client.cookies.delete(FAMILY_COOKIE)

    response = live_client.request(method, path, json=body)

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "family.no_session"
