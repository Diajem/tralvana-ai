"""FastAPI dependencies and ownership guards for authenticated resources."""

from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException, Request, status

from app.auth.clerk import AuthenticatedTraveller, ClerkAuthenticator
from app.auth.config import AuthSettings


@lru_cache(maxsize=1)
def authenticator() -> ClerkAuthenticator:
    return ClerkAuthenticator(AuthSettings.from_environment())


def reset_authenticator() -> None:
    """Re-read environment-backed auth configuration in tests."""
    authenticator.cache_clear()


async def require_authenticated_traveller(
    request: Request,
) -> AuthenticatedTraveller | None:
    principal = authenticator().authenticate(request)
    if authenticator().enabled and principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid Clerk session is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal


def require_owner(
    principal: AuthenticatedTraveller | None,
    traveller_id: str | None,
) -> None:
    """Reject cross-account access while preserving disabled local/test mode."""
    if principal is not None and traveller_id != principal.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource belongs to another traveller",
        )


def authenticated_traveller_id(
    principal: AuthenticatedTraveller | None,
    requested_traveller_id: str | None,
) -> str | None:
    """Bind a request to its verified identity when Clerk is enabled."""
    if principal is None:
        return requested_traveller_id
    # Never trust or require a client-supplied identity for a write. Legacy
    # clients may still send traveller_id, but the verified Clerk subject is
    # the sole owner used by the service.
    return principal.user_id


def require_trip_owner(
    principal: AuthenticatedTraveller | None,
    trip_id: str | None,
) -> None:
    if principal is None or trip_id is None:
        return
    from app.domains.trips.service import trip_planning_service

    trip = trip_planning_service.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    require_owner(principal, trip.get("traveller_id"))


def require_goal_owner(
    principal: AuthenticatedTraveller | None,
    goal_id: str | None,
) -> None:
    if principal is None or goal_id is None:
        return
    from app.domains.goals.service import goal_service

    goal = goal_service.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    require_owner(principal, goal.get("traveller_id"))


def require_conversation_owner(
    principal: AuthenticatedTraveller | None,
    conversation_id: str | None,
) -> None:
    if principal is None or conversation_id is None:
        return
    from ai.concierge.conversation_engine import conversation_engine

    session = conversation_engine.get_session(conversation_id)
    if session is not None:
        require_owner(principal, session.traveller_id)


def require_resource_owner(
    principal: AuthenticatedTraveller | None,
    resource: dict | None,
) -> None:
    if principal is None or resource is None:
        return
    traveller_id = resource.get("traveller_id")
    if traveller_id:
        require_owner(principal, traveller_id)
        return
    trip_id = resource.get("trip_id")
    if trip_id:
        require_trip_owner(principal, trip_id)
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This resource is not assigned to the authenticated traveller",
    )
