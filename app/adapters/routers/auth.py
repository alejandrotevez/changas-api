from __future__ import annotations

import dataclasses

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.middleware.auth import get_current_user
from app.adapters.repositories.user_repo import UserRepository
from app.adapters.schemas.auth import (
    GoogleLoginRequest,
    LoginRequest,
    LoginResponse,
    UpdateUserRequest,
    UsuarioResponse,
)
from app.domain.entities import Usuario
from app.domain.exceptions import AuthenticationError
from app.framework.database import get_db
from app.usecases.auth import LoginUseCase, TokenService

router = APIRouter(tags=["auth"])

# Stateless helpers — safe to create once at module level.
_token_service = TokenService()


def _get_login_use_case(db: AsyncSession = Depends(get_db)) -> LoginUseCase:
    repo = UserRepository(db)
    return LoginUseCase(repo, _token_service)


@router.post(
    "/auth/login/email",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login_email(
    body: LoginRequest,
    use_case: LoginUseCase = Depends(_get_login_use_case),
) -> LoginResponse:
    try:
        result = await use_case.execute_email(body.email, body.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return LoginResponse(
        usuario=UsuarioResponse.model_validate(result.usuario),
        token=result.token,
    )


@router.post(
    "/auth/login/google",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login_google(
    body: GoogleLoginRequest,
    use_case: LoginUseCase = Depends(_get_login_use_case),
) -> LoginResponse:
    try:
        result = await use_case.execute_google(body.id_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return LoginResponse(
        usuario=UsuarioResponse.model_validate(result.usuario),
        token=result.token,
    )


@router.patch(
    "/users/me",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
)
async def update_me(
    body: UpdateUserRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    update_data: dict = {}
    if body.rol_actual is not None:
        update_data["rol_actual"] = body.rol_actual
    if body.tags is not None:
        update_data["tags"] = body.tags

    if not update_data:
        return UsuarioResponse.model_validate(current_user)

    updated = dataclasses.replace(current_user, **update_data)
    repo = UserRepository(db)
    saved = await repo.update(updated)
    return UsuarioResponse.model_validate(saved)
