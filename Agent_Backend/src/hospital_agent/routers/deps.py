import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from hospital_agent.core.config import Settings, get_settings
from hospital_agent.core.security import decode_access_token
from hospital_agent.db.session import get_session
from hospital_agent.db.unit_of_work import UnitOfWork
from hospital_agent.integrations.email.factory import create_email_sender
from hospital_agent.integrations.email.port import EmailSender
from hospital_agent.models.user import User, UserRole
from hospital_agent.services.auth_service import AuthService
from hospital_agent.services.onboarding_service import OnboardingService

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_uow(session: SessionDep) -> UnitOfWork:
    return UnitOfWork(session)


UowDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_email_sender(settings: SettingsDep) -> EmailSender:
    return create_email_sender(settings)


def get_auth_service(uow: UowDep, settings: SettingsDep) -> AuthService:
    return AuthService(uow, settings)


def get_onboarding_service(
    uow: UowDep,
    email: Annotated[EmailSender, Depends(get_email_sender)],
    settings: SettingsDep,
) -> OnboardingService:
    return OnboardingService(uow, email, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
OnboardingServiceDep = Annotated[OnboardingService, Depends(get_onboarding_service)]

_unauthenticated = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
)


async def get_current_user(request: Request, settings: SettingsDep, auth: AuthServiceDep) -> User:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise _unauthenticated
    try:
        user_id = uuid.UUID(decode_access_token(token, settings)["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise _unauthenticated from None
    user = await auth.get_active_user(user_id)
    if user is None:
        raise _unauthenticated
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Dependency factory: `Depends(require_role(UserRole.PLATFORM_ADMIN))`."""

    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return checker
