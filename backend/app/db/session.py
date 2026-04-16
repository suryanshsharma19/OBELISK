"""SQLAlchemy engine & session factory."""

from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

database_url = os.getenv("DATABASE_URL") or settings.postgres_url

engine_kwargs = {
    "echo": settings.debug,
    "pool_pre_ping": True,
}

# SQLite needs this flag when used with a threaded ASGI server.
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    database_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
