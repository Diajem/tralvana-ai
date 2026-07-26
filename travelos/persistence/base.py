"""Shared SQLAlchemy metadata for TravelOS-owned relational tables."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by API and AI persistence adapters."""
