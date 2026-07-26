"""Networkless Clerk session-token verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions

from app.auth.config import AuthMode, AuthSettings


@dataclass(frozen=True)
class AuthenticatedTraveller:
    """Identity derived exclusively from a verified Clerk session token."""

    user_id: str
    session_id: str | None = None


class RequestWithHeaders(Protocol):
    @property
    def headers(self) -> Any: ...


class ClerkAuthenticator:
    """Authenticate API requests without calling Clerk on each request."""

    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.mode is AuthMode.CLERK

    def authenticate(self, request: RequestWithHeaders) -> AuthenticatedTraveller | None:
        if not self.enabled:
            return None

        state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                jwt_key=self._settings.jwt_key,
                authorized_parties=list(self._settings.authorized_parties),
                accepts_token=["session_token"],
            ),
        )
        if not state.is_signed_in or not state.payload:
            return None

        subject = state.payload.get("sub")
        if not isinstance(subject, str) or not subject:
            return None
        session_id = state.payload.get("sid")
        return AuthenticatedTraveller(
            user_id=subject,
            session_id=session_id if isinstance(session_id, str) else None,
        )
