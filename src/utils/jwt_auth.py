# ruff: noqa: TC002

import uuid
from typing import Annotated

from fastapi import HTTPException
from fastapi import Security
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from src.models.users import User
from src.utils.auth_tokens import validate_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(dependency=_bearer_scheme)],
) -> User:
    """Get Current User From Access Token.

    Arguments:
        credentials (HTTPAuthorizationCredentials | None): Authorization header credentials.

    Returns:
        User: Authenticated user.

    Raises:
        HTTPException: If token is missing/invalid/expired or user cannot be loaded.
    """

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token: str = credentials.credentials

    token_status: str
    payload: dict[str, object] | None
    token_status, payload = await validate_access_token(token=token)

    if token_status != "valid" or payload is None:  # noqa: S105
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    raw_user_id: object = payload.get("sub")
    if not isinstance(raw_user_id, str) or not raw_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    try:
        user_uuid: uuid.UUID = uuid.UUID(hex=raw_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from exc

    try:
        postgresql_adapter: PostgreSQLAdapter = await get_postgresql_adapter()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(object=exc),
        ) from exc

    session: AsyncSession = await postgresql_adapter.get_session()

    async with session as db:
        result: Result[tuple[User]] = await db.execute(statement=select(User).where(User.id == user_uuid))
        user: User | None = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    return user


__all__: list[str] = ["get_current_user"]
