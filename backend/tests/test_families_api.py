import hashlib
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.core.deps import get_settings
from jumbaq.families.deps import FAMILY_COOKIE
from jumbaq.families.models import FamilyRow
from tests.conftest import TEST_SETTINGS
from tests.flows import create_family, family_body

pytestmark = pytest.mark.integration


async def test_creating_a_family_sets_the_cookie_and_stores_only_its_hash(
    live_client: TestClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    response = live_client.post("/api/v1/families", json=family_body())

    assert response.status_code == 201
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{FAMILY_COOKIE}=")
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/api/v1" in cookie
    token = response.cookies[FAMILY_COOKIE]
    async with sessionmaker() as session:
        row = await session.get(FamilyRow, uuid.UUID(response.json()["id"]))
    assert row is not None
    assert row.session_token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert token not in row.session_token_hash


def test_the_family_of_the_cookie(live_client: TestClient) -> None:
    family_id, _ = create_family(live_client)

    response = live_client.get("/api/v1/family")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(family_id)
    assert [(kid["nickname"], kid["age"]) for kid in body["kids"]] == [("Aru", 7), ("Timur", 9)]
    assert body["rooms"] == ["kitchen", "living room", "bedroom"]
    assert body["objects"] == ["fridge", "sofa", "bookshelf", "kettle"]
    assert body["demo_mode"] is True


def test_without_a_cookie_there_is_no_family(live_client: TestClient) -> None:
    response = live_client.get("/api/v1/family")

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "family.no_session"
    assert error["request_id"] == response.headers["x-request-id"]


def test_an_unknown_cookie_gives_the_same_answer(live_client: TestClient) -> None:
    live_client.cookies.set(FAMILY_COOKIE, "not-a-session", domain="testserver.local")

    response = live_client.get("/api/v1/family")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "family.no_session"


def test_another_family_sees_only_its_own(live_client: TestClient) -> None:
    first_id, first_token = create_family(live_client)
    second_id, _ = create_family(live_client, kids=[{"nickname": "Dana", "age": 5}])

    live_client.cookies.clear()
    live_client.cookies.set(FAMILY_COOKIE, first_token, domain="testserver.local")
    response = live_client.get("/api/v1/family")

    assert response.json()["id"] == str(first_id) != str(second_id)


def test_repeated_nicknames_are_refused(live_client: TestClient) -> None:
    body = family_body(kids=[{"nickname": "Aru", "age": 7}, {"nickname": " aru ", "age": 9}])

    response = live_client.post("/api/v1/families", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["fields"] == {"kids": "family.kid_nickname_repeated"}
    assert FAMILY_COOKIE not in response.cookies


def test_a_change_without_the_header_of_the_web_app_is_refused(client: TestClient) -> None:
    response = client.post("/api/v1/families", json=family_body(), headers={"X-Requested-With": ""})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "common.forbidden"


def test_the_family_says_whether_demo_mode_is_on(live_client: TestClient) -> None:
    create_family(live_client)
    assert live_client.get("/api/v1/family").json()["demo_mode"] is True

    no_demo = TEST_SETTINGS.model_copy(update={"demo_mode": False})
    live_client.app.dependency_overrides[get_settings] = lambda: no_demo  # type: ignore[attr-defined]
    try:
        body = live_client.get("/api/v1/family").json()
    finally:
        live_client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
    assert body["demo_mode"] is False
