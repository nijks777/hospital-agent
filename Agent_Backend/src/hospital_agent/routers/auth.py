from fastapi import APIRouter, HTTPException, Response, status

from hospital_agent.models.hospital import HospitalStatus
from hospital_agent.routers.deps import AuthServiceDep, CurrentUser, SettingsDep
from hospital_agent.schemas.auth import LoginRequest
from hospital_agent.schemas.user import UserRead
from hospital_agent.services.auth_service import HospitalNotActiveError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])

_NOT_ACTIVE_MESSAGES = {
    HospitalStatus.PENDING_VERIFICATION: "Verify your email to finish registering your hospital.",
    HospitalStatus.PENDING_REVIEW: (
        "Your hospital's application is under review. You can sign in once it's approved."
    ),
    HospitalStatus.REJECTED: "Your hospital's application was not approved.",
    HospitalStatus.SUSPENDED: "This hospital's account is suspended. Contact support.",
}


@router.post("/login")
async def login(
    body: LoginRequest, response: Response, auth: AuthServiceDep, settings: SettingsDep
) -> UserRead:
    try:
        user, token = await auth.login(body.username, body.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password"
        ) from None
    except HospitalNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=_NOT_ACTIVE_MESSAGES[exc.status]
        ) from None
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,  # JavaScript can't read it → XSS can't steal it
        secure=not settings.is_local,  # HTTPS only outside local dev
        samesite="lax",  # not sent on cross-site POSTs → basic CSRF protection
        path="/",
    )
    return UserRead.model_validate(user, from_attributes=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, settings: SettingsDep) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/")


@router.get("/me")
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user, from_attributes=True)
