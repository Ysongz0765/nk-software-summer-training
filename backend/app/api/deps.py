from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise PermissionDeniedError("invalid or expired token")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise PermissionDeniedError("invalid token subject")

    user = (
        db.query(User)
        .filter(or_(User.username == subject, User.email == subject))
        .one_or_none()
    )
    if user is None or not user.is_active:
        raise PermissionDeniedError("user is inactive or not found")
    return user


def get_current_user(
    user: Annotated[User | None, Depends(get_optional_current_user)],
) -> User:
    if user is None:
        raise PermissionDeniedError("authentication required")
    return user
