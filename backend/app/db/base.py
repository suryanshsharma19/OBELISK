"""Declarative base + timestamp mixin."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, declared_attr


def _utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


class Base(TimestampMixin, DeclarativeBase):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
