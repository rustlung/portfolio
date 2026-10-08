from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Project
from app.services import project_screenshots as screenshot_storage


@pytest.fixture()
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture()
def client(
    session_factory: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    uploads_dir = tmp_path / "uploads" / "project_screenshots"
    monkeypatch.setattr(screenshot_storage, "SCREENSHOTS_UPLOAD_DIR", uploads_dir)

    def override_get_db() -> Iterator[Session]:
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(client: TestClient) -> TestClient:
    response = client.post(
        "/admin/login",
        data={"password": settings.admin_password},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client


def create_project(db: Session, *, slug: str = "test-project") -> Project:
    project = Project(
        title="Test Project",
        slug=slug,
        short_description="Short description",
        full_description="Full description",
        problem="Problem",
        features="Features",
        result="Result",
        practical_use="Practical use",
        technologies="FastAPI",
        sort_order=0,
        is_featured=False,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
