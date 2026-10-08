import logging

from fastapi import APIRouter, HTTPException, status

from hospital_agent.integrations.email.port import EmailDeliveryError
from hospital_agent.routers.deps import OnboardingServiceDep
from hospital_agent.schemas.onboarding import (
    RegisterHospitalRequest,
    RegisterHospitalResponse,
    ResendCodeRequest,
    VerifyEmailRequest,
)
from hospital_agent.services.onboarding_service import (
    CodeExpiredError,
    EmailAlreadyRegisteredError,
    InvalidCodeError,
    ResendTooSoonError,
    TooManyAttemptsError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

_email_failed = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="We couldn't send the verification email. Try again in a minute.",
)


def _too_soon(exc: ResendTooSoonError) -> HTTPException:
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Wait {exc.retry_after_seconds} seconds before sending another code.",
        headers={"Retry-After": str(exc.retry_after_seconds)},
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterHospitalRequest, onboarding: OnboardingServiceDep
) -> RegisterHospitalResponse:
    try:
        hospital = await onboarding.register(body)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Sign in instead.",
        ) from None
    except ResendTooSoonError as exc:
        raise _too_soon(exc) from None
    except EmailDeliveryError:
        logger.exception("Verification email failed during registration")
        raise _email_failed from None
    return RegisterHospitalResponse(hospital_id=hospital.id, email=body.email)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(body: VerifyEmailRequest, onboarding: OnboardingServiceDep) -> None:
    try:
        await onboarding.verify_email(body.email, body.code)
    except InvalidCodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That code is incorrect.") from None
    except CodeExpiredError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This code has expired. Send a new code."
        ) from None
    except TooManyAttemptsError:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many incorrect attempts. Send a new code."
        ) from None


@router.post("/resend-code", status_code=status.HTTP_202_ACCEPTED)
async def resend_code(body: ResendCodeRequest, onboarding: OnboardingServiceDep) -> None:
    try:
        await onboarding.resend_code(body.email)
    except ResendTooSoonError as exc:
        raise _too_soon(exc) from None
    except EmailDeliveryError:
        logger.exception("Verification email failed during resend")
        raise _email_failed from None
