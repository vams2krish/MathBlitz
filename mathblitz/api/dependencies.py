"""FastAPI dependency adapters."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..core.container import Container
from ..db.models import User
from ..db.repositories import UserRepository


def container_from(request: Request) -> Container:
    return request.app.state.container


def session_from(
    container: Annotated[Container, Depends(container_from)],
) -> Iterator[Session]:
    with container.sessions() as session:
        yield session


def current_user(
    authorization: Annotated[str | None, Header()] = None,
    container: Annotated[Container, Depends(container_from)] = None,
    session: Annotated[Session, Depends(session_from)] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A bearer token is required.",
        )
    user_id = container.authentication.tokens.subject(authorization[7:])
    user = UserRepository(session).by_id(user_id) if user_id else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token is invalid or expired.",
        )
    return user


ContainerDependency = Annotated[Container, Depends(container_from)]
SessionDependency = Annotated[Session, Depends(session_from)]
CurrentUser = Annotated[User, Depends(current_user)]
