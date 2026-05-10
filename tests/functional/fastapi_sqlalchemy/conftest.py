"""Shared fixtures for FastAPI + SQLAlchemy functional tests."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base model for FastAPI + SQLAlchemy functional tests."""


class User(Base):
    """Mapped test model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
