from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppError, PermissionDeniedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserRead
from app.schemas.common import ApiResponse

router = APIRouter()


@router.post("/register", response_model=ApiResponse[AuthResponse])
async def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AuthResponse]:
    username = payload.username.strip()
    email = payload.email.strip().lower()

    existing = (
        db.query(User)
        .filter(or_(User.username == username, User.email == email))
        .one_or_none()
    )
    if existing is not None:
        raise AppError("username or email already exists")

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ApiResponse(data=_auth_response(user))


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AuthResponse]:
    username = payload.username.strip()
    user = (
        db.query(User)
        .filter(or_(User.username == username, User.email == username.lower()))
        .one_or_none()
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise PermissionDeniedError("invalid username or password")
    if not user.is_active:
        raise PermissionDeniedError("user is inactive")

    return ApiResponse(data=_auth_response(user))


@router.get("/me", response_model=ApiResponse[UserRead])
async def me(
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[UserRead]:
    return ApiResponse(data=_user_read(user))


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(user.username),
        user=_user_read(user),
    )


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
    )
