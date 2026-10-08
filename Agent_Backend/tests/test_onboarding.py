from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from hospital_agent.core.config import get_settings
from hospital_agent.main import create_app
from hospital_agent.models.base import utcnow
from hospital_agent.models.hospital import Hospital, HospitalStatus, InvalidStatusTransitionError
from hospital_agent.routers.deps import get_onboarding_service
from hospital_agent.services.onboarding_service import OnboardingService
from tests.fakes import FakeEmailSender, FakeUnitOfWork

FORM = {
    "hospital_name": "City Care Hospital",
    "city": "Pune",
    "contact_name": "Asha Rao",
    "email": "Admin@CityCare.in",
    "phone": "+91 98765 43210",
    "password": "strong-pass-1",
}


class Harness:
    def __init__(self, email_fails: bool = False) -> None:
        self.uow = FakeUnitOfWork()
        self.email = FakeEmailSender(fail=email_fails)
        service = OnboardingService(self.uow, self.email, get_settings())  # pyright: ignore[reportArgumentType]
        app = create_app()
        app.dependency_overrides[get_onboarding_service] = lambda: service
        self.client = TestClient(app)

    def register(self) -> None:
        assert self.client.post("/onboarding/register", json=FORM).status_code == 201

    def verify(self, code: str) -> int:
        return self.client.post(
            "/onboarding/verify-email", json={"email": FORM["email"], "code": code}
        ).status_code

    @property
    def hospital(self) -> Hospital:
        return next(iter(self.uow.hospitals.rows.values()))


def test_register_creates_pending_hospital_and_admin_and_emails_code() -> None:
    h = Harness()

    response = h.client.post("/onboarding/register", json=FORM)

    assert response.status_code == 201
    assert h.hospital.status == HospitalStatus.PENDING_VERIFICATION
    user = next(iter(h.uow.users.rows.values()))
    assert user.username == user.email == "admin@citycare.in"  # normalised to lowercase
    assert user.password_hash != FORM["password"]
    assert h.email.sent[0].to == "admin@citycare.in"
    assert h.email.last_code().isdigit() and len(h.email.last_code()) == 6
    assert h.uow.commits == 1


def test_code_is_stored_hashed_not_plain() -> None:
    h = Harness()
    h.register()

    assert h.uow.email_verifications.rows[0].code_hash != h.email.last_code()


def test_register_does_not_save_when_email_fails() -> None:
    h = Harness(email_fails=True)

    response = h.client.post("/onboarding/register", json=FORM)

    assert response.status_code == 503
    assert h.uow.commits == 0


def test_register_rejects_duplicate_email() -> None:
    h = Harness()
    h.register()

    response = h.client.post("/onboarding/register", json=FORM)

    assert response.status_code == 409


@pytest.mark.parametrize(
    ("field", "value"),
    [("email", "not-an-email"), ("phone", "abc"), ("password", "short"), ("city", " ")],
)
def test_register_validates_input(field: str, value: str) -> None:
    response = Harness().client.post("/onboarding/register", json={**FORM, field: value})

    assert response.status_code == 422


def test_correct_code_moves_hospital_to_pending_review() -> None:
    h = Harness()
    h.register()

    assert h.verify(h.email.last_code()) == 204
    assert h.hospital.status == HospitalStatus.PENDING_REVIEW
    assert next(iter(h.uow.users.rows.values())).email_verified_at is not None


def test_wrong_code_is_rejected_and_counted() -> None:
    h = Harness()
    h.register()
    wrong = "000000" if h.email.last_code() != "000000" else "111111"

    assert h.verify(wrong) == 400
    assert h.uow.email_verifications.rows[0].attempts == 1
    assert h.hospital.status == HospitalStatus.PENDING_VERIFICATION


def test_too_many_wrong_attempts_locks_the_code() -> None:
    h = Harness()
    h.register()
    h.uow.email_verifications.rows[0].attempts = get_settings().verification_max_attempts

    assert h.verify(h.email.last_code()) == 429


def test_expired_code_is_rejected() -> None:
    h = Harness()
    h.register()
    h.uow.email_verifications.rows[0].expires_at = utcnow() - timedelta(seconds=1)

    assert h.verify(h.email.last_code()) == 400


def test_resend_is_rate_limited() -> None:
    h = Harness()
    h.register()

    response = h.client.post("/onboarding/resend-code", json={"email": FORM["email"]})

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_resend_after_cooldown_sends_new_code_and_old_one_stops_working() -> None:
    h = Harness()
    h.register()
    old_code = h.email.last_code()
    h.uow.email_verifications.rows[0].created_at = utcnow() - timedelta(minutes=5)

    response = h.client.post("/onboarding/resend-code", json={"email": FORM["email"]})

    assert response.status_code == 202
    assert len(h.email.sent) == 2
    if old_code != h.email.last_code():
        assert h.verify(old_code) == 400
    assert h.verify(h.email.last_code()) == 204


def test_resend_for_unknown_email_reveals_nothing() -> None:
    h = Harness()

    response = h.client.post("/onboarding/resend-code", json={"email": "nobody@example.com"})

    assert response.status_code == 202
    assert h.email.sent == []


def test_status_machine_blocks_invalid_moves() -> None:
    hospital = Hospital(
        name="X",
        city="Y",
        contact_name="Z",
        contact_phone="1234567",
        status=HospitalStatus.REJECTED,
    )

    with pytest.raises(InvalidStatusTransitionError):
        hospital.transition_to(HospitalStatus.ACTIVE)
