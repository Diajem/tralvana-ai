"""Authentication boundary for Tralvana's Clerk integration."""

from app.auth.dependencies import AuthenticatedTraveller, require_authenticated_traveller

__all__ = ["AuthenticatedTraveller", "require_authenticated_traveller"]
