from fastapi.testclient import TestClient

from hospital_agent.db.session import get_session
from hospital_agent.main import create_app


class FakeSession:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    async def exec(self, statement: object) -> None:
        if self.fail:
            raise ConnectionError("db down")


def client_with_session(session: FakeSession) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def test_health_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_database_reachable() -> None:
    response = client_with_session(FakeSession()).get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_ready_returns_503_when_database_down() -> None:
    response = client_with_session(FakeSession(fail=True)).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down"}
