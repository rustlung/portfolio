import base64
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import Project, ProjectScreenshot
from app.services import project_screenshots as screenshot_storage
from tests.conftest import create_project


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def test_project_screenshot_record_can_be_created(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        project = create_project(db)
        screenshot = ProjectScreenshot(
            project_id=project.id,
            image_path="/static/uploads/project_screenshots/example.png",
            caption="Overview",
            sort_order=3,
        )
        db.add(screenshot)
        db.commit()
        db.refresh(screenshot)

        assert screenshot.id is not None
        assert screenshot.project_id == project.id
        assert screenshot.caption == "Overview"


def test_public_gallery_is_sorted_and_hidden_when_empty(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        project = create_project(db, slug="with-gallery")
        empty_project = create_project(db, slug="without-gallery")
        db.add_all(
            [
                ProjectScreenshot(
                    project_id=project.id,
                    image_path="/static/uploads/project_screenshots/third.png",
                    caption="Third",
                    sort_order=20,
                ),
                ProjectScreenshot(
                    project_id=project.id,
                    image_path="/static/uploads/project_screenshots/first.png",
                    caption="First",
                    sort_order=10,
                ),
                ProjectScreenshot(
                    project_id=project.id,
                    image_path="/static/uploads/project_screenshots/second.png",
                    caption="Second",
                    sort_order=10,
                ),
            ]
        )
        db.commit()

    gallery_response = client.get("/projects/with-gallery")
    assert gallery_response.status_code == 200
    assert "Скриншоты проекта" in gallery_response.text
    assert "/static/js/project_gallery.js" in gallery_response.text
    assert gallery_response.text.index("First") < gallery_response.text.index("Second")
    assert gallery_response.text.index("Second") < gallery_response.text.index("Third")

    empty_response = client.get(f"/projects/{empty_project.slug}")
    assert empty_response.status_code == 200
    assert "Скриншоты проекта" not in empty_response.text
    assert "data-project-gallery" not in empty_response.text
    assert "/static/js/project_gallery.js" not in empty_response.text


def test_unauthenticated_gallery_management_is_rejected(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        project = create_project(db)

    response = client.get(
        f"/admin/projects/{project.id}/screenshots",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_unsupported_upload_is_rejected_without_writing_a_file(
    admin_client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        project = create_project(db)

    response = admin_client.post(
        f"/admin/projects/{project.id}/screenshots/upload",
        files={"images": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert "не является поддерживаемым изображением" in response.text
    with session_factory() as db:
        assert db.scalar(select(ProjectScreenshot)) is None
    assert not screenshot_storage.SCREENSHOTS_UPLOAD_DIR.exists()


def test_upload_edit_and_delete_screenshot_and_file(
    admin_client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        project = create_project(db)

    upload_response = admin_client.post(
        f"/admin/projects/{project.id}/screenshots/upload",
        files=[
            ("images", ("one.png", PNG_BYTES, "image/png")),
            ("images", ("two.png", PNG_BYTES, "image/png")),
        ],
        follow_redirects=False,
    )
    assert upload_response.status_code == 303

    with session_factory() as db:
        screenshots = list(
            db.scalars(
                select(ProjectScreenshot).order_by(ProjectScreenshot.sort_order)
            )
        )
        assert len(screenshots) == 2
        screenshot = screenshots[0]
        image_path = screenshot_storage.SCREENSHOTS_UPLOAD_DIR / Path(screenshot.image_path).name
        assert image_path.read_bytes() == PNG_BYTES
        assert screenshot.image_path.startswith(screenshot_storage.PUBLIC_SCREENSHOTS_PREFIX)

    edit_response = admin_client.post(
        f"/admin/projects/{project.id}/screenshots/{screenshot.id}/edit",
        data={"caption": "  Main screen  ", "sort_order": "42"},
        follow_redirects=False,
    )
    assert edit_response.status_code == 303

    with session_factory() as db:
        edited = db.get(ProjectScreenshot, screenshot.id)
        assert edited is not None
        assert edited.caption == "Main screen"
        assert edited.sort_order == 42

    delete_response = admin_client.post(
        f"/admin/projects/{project.id}/screenshots/{screenshot.id}/delete",
        follow_redirects=False,
    )
    assert delete_response.status_code == 303
    assert not image_path.exists()
    with session_factory() as db:
        assert db.get(ProjectScreenshot, screenshot.id) is None


def test_deleting_project_cascades_gallery_and_removes_only_its_files(
    admin_client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    screenshot_storage.SCREENSHOTS_UPLOAD_DIR.mkdir(parents=True)
    first_file = screenshot_storage.SCREENSHOTS_UPLOAD_DIR / "first.png"
    second_file = screenshot_storage.SCREENSHOTS_UPLOAD_DIR / "second.png"
    first_file.write_bytes(PNG_BYTES)
    second_file.write_bytes(PNG_BYTES)

    with session_factory() as db:
        first_project = create_project(db, slug="first-project")
        second_project = create_project(db, slug="second-project")
        first_screenshot = ProjectScreenshot(
            project_id=first_project.id,
            image_path=f"{screenshot_storage.PUBLIC_SCREENSHOTS_PREFIX}{first_file.name}",
            sort_order=0,
        )
        second_screenshot = ProjectScreenshot(
            project_id=second_project.id,
            image_path=f"{screenshot_storage.PUBLIC_SCREENSHOTS_PREFIX}{second_file.name}",
            sort_order=0,
        )
        db.add_all([first_screenshot, second_screenshot])
        db.commit()
        first_screenshot_id = first_screenshot.id
        second_screenshot_id = second_screenshot.id

    response = admin_client.post(
        f"/admin/projects/{first_project.id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert not first_file.exists()
    assert second_file.exists()
    with session_factory() as db:
        assert db.get(ProjectScreenshot, first_screenshot_id) is None
        assert db.get(ProjectScreenshot, second_screenshot_id) is not None
        assert db.get(Project, second_project.id) is not None


def test_create_all_adds_gallery_table_without_losing_existing_projects(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "existing.db"
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    Project.__table__.create(engine)
    factory = sessionmaker(bind=engine)

    with factory() as db:
        project = create_project(db, slug="existing-project")
        existing_project_id = project.id

    Base.metadata.create_all(engine)

    assert "project_screenshots" in inspect(engine).get_table_names()
    with factory() as db:
        existing_project = db.get(Project, existing_project_id)
        assert existing_project is not None
        assert existing_project.slug == "existing-project"

    engine.dispose()
