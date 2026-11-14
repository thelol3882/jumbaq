import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from jumbaq.core.deps import get_engine, get_redis


class _FakeConnection:
    async def execute(self, _statement):
        return None


class _FakeEngine:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    @asynccontextmanager
    async def connect(self):
        await asyncio.sleep(0)
        if self.fail:
            raise ConnectionRefusedError("database is down")
        yield _FakeConnection()


class _FakeRedis:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    async def ping(self) -> bool:
        if self.fail:
            raise ConnectionRefusedError("redis is down")
        return True


def _use_fakes(app: FastAPI, engine: _FakeEngine, redis: _FakeRedis) -> None:
    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[get_redis] = lambda: redis


def test_health_is_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_everything_answers(app: FastAPI, client: TestClient) -> None:
    _use_fakes(app, _FakeEngine(), _FakeRedis())

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}


def test_not_ready_when_the_database_is_down(app: FastAPI, client: TestClient) -> None:
    _use_fakes(app, _FakeEngine(fail=True), _FakeRedis())

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["checks"] == {"database": "fail", "redis": "ok"}
