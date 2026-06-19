"""Database engine, declarative base and request-scoped session helpers."""

from _collections_abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

# SessionLocal is used to open short-lived DB sessions inside request handlers.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_db() -> Generator[Session, None, None]:
    """Yield one SQLAlchemy session per request and close it afterwards."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
