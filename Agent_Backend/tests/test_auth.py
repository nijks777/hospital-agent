import uuid
from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from hospital_agent.core.config import get_settings
from hospital_agent.core.security import create_access_token, hash_password
from hospital_agent.main import create_app
from hospital_agent.models.hospital import Hospital, HospitalStatus
from hospital_agent.models.user import User, UserRole
from hospital_agent.routers.deps import get_auth_service, get_current_user, require_role
from hospital_agent.services.auth_service import AuthService
from tests.fakes import FakeUnitOfWork

PASSWORD = "correct-horse"


def make_user(role: UserRole = UserRole.PLATFORM_ADMIN, *, active: bool = True) -> User:
    return User(
        username="sadmin", password_hash=hash_password(PASSWORD), role=role, is_active=active
    )


def make_client(*users: User, hospitals: tuple[Hospital, ...] = ()) -> TestClient:
    app = create_app()
    uow = FakeUnitOfWork(*users, hospitals=hospitals)
    service = AuthService(uow, get_settings())  # pyright: ignore[reportArgumentType]
    app.dependency_overrides[get_auth_service] = lambda: service
    return TestClient(app)


def test_login_sets_httponly_cookie_and_returns_user_without_password() -> None:
    client = make_client(make_user())

    response = client.post("/auth/login", json={"username": "sadmin", "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "sadmin"
    assert body["role"] == "platform_admin"
    assert "password_hash" not in body
    cookie = response.headers["set-cookie"]
    assert "access_token=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


@pytest.mark.parametrize(("username", "password"), [("sadmin", "wrong"), ("nobody", PASSWORD)])
def test_login_rejects_bad_credentials_with_same_message(username: str, password: str) -> None:
    client = make_client(make_user())

    response = client.post("/auth/login", json={"username": username, "password": password})

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_login_rejects_inactive_user() -> None:
    client = make_client(make_user(active=False))

    response = client.post("/auth/login", json={"username": "sadmin", "password": PASSWORD})

    assert response.status_code == 401


def test_me_returns_user_after_login() -> None:
    client = make_client(make_user())
    client.post("/auth/login", json={"username": "sadmin", "password": PASSWORD})

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "sadmin"


@pytest.mark.parametrize("cookie", [None, "not-a-jwt"])
def test_me_requires_valid_token(cookie: str | None) -> None:
    client = make_client(make_user())
    if cookie:
        client.cookies.set("access_token", cookie)

    assert client.get("/auth/me").status_code == 401


def test_token_for_deleted_user_is_rejected() -> None:
    client = make_client()  # repository has no users
    token = create_access_token(uuid.uuid4(), "platform_admin", get_settings())
    client.cookies.set("access_token", token)

    assert client.get("/auth/me").status_code == 401


def test_logout_clears_cookie() -> None:
    client = make_client(make_user())
    client.post("/auth/login", json={"username": "sadmin", "password": PASSWORD})

    client.post("/auth/logout")

    assert client.get("/auth/me").status_code == 401


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [(UserRole.PLATFORM_ADMIN, 200), (UserRole.HOSPITAL_ADMIN, 403)],
)
def test_require_role(role: UserRole, expected_status: int) -> None:
    app = create_app()
    checker = require_role(UserRole.PLATFORM_ADMIN)

    @app.get("/test/platform-only")
    async def platform_only(_: Annotated[User, Depends(checker)]) -> dict[str, bool]:
        return {"ok": True}

    app.dependency_overrides[get_current_user] = lambda: make_user(role)

    assert TestClient(app).get("/test/platform-only").status_code == expected_status


def make_hospital_admin(status: HospitalStatus) -> tuple[User, Hospital]:
    hospital = Hospital(
        name="City Care", city="Pune", contact_name="A", contact_phone="9876543210", status=status
    )
    user = User(
        username="admin@citycare.in",
        email="admin@citycare.in",
        password_hash=hash_password(PASSWORD),
        role=UserRole.HOSPITAL_ADMIN,
        hospital_id=hospital.id,
    )
    return user, hospital


def test_hospital_admin_of_active_hospital_can_log_in() -> None:
    user, hospital = make_hospital_admin(HospitalStatus.ACTIVE)
    client = make_client(user, hospitals=(hospital,))

    response = client.post(
        "/auth/login", json={"username": "Admin@CityCare.in", "password": PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "hospital_admin"


@pytest.mark.parametrize(
    ("status", "message_part"),
    [
        (HospitalStatus.PENDING_VERIFICATION, "Verify your email"),
        (HospitalStatus.PENDING_REVIEW, "under review"),
        (HospitalStatus.REJECTED, "not approved"),
        (HospitalStatus.SUSPENDED, "suspended"),
    ],
)
def test_hospital_admin_blocked_until_hospital_active(
    status: HospitalStatus, message_part: str
) -> None:
    user, hospital = make_hospital_admin(status)
    client = make_client(user, hospitals=(hospital,))

    response = client.post(
        "/auth/login", json={"username": "admin@citycare.in", "password": PASSWORD}
    )

    assert response.status_code == 403
    assert message_part in response.json()["detail"]
    assert "set-cookie" not in response.headers


def test_wrong_password_for_pending_hospital_still_says_incorrect() -> None:
    user, hospital = make_hospital_admin(HospitalStatus.PENDING_REVIEW)
    client = make_client(user, hospitals=(hospital,))

    response = client.post("/auth/login", json={"username": "admin@citycare.in", "password": "x"})

    assert response.status_code == 401


def test_existing_session_stops_working_when_hospital_is_suspended() -> None:
    user, hospital = make_hospital_admin(HospitalStatus.ACTIVE)
    client = make_client(user, hospitals=(hospital,))
    client.post("/auth/login", json={"username": "admin@citycare.in", "password": PASSWORD})
    assert client.get("/auth/me").status_code == 200

    hospital.transition_to(HospitalStatus.SUSPENDED)

    assert client.get("/auth/me").status_code == 401
