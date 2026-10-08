"""Admin routes for managing screenshots attached to one project."""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Project, ProjectScreenshot
from app.services import project_screenshots as screenshot_storage


router = APIRouter(prefix="/admin/projects", tags=["admin-project-screenshots"])
templates = Jinja2Templates(directory="app/templates")


def get_project(db: Session, project_id: int) -> Project | None:
    return db.execute(
        select(Project).where(Project.id == project_id)
    ).scalar_one_or_none()


def get_project_screenshots(db: Session, project_id: int) -> list[ProjectScreenshot]:
    return list(
        db.execute(
            select(ProjectScreenshot)
            .where(ProjectScreenshot.project_id == project_id)
            .order_by(ProjectScreenshot.sort_order, ProjectScreenshot.id)
        ).scalars()
    )


def render_gallery_manager(
    request: Request,
    db: Session,
    project: Project,
    *,
    error: str | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request=request,
        name="admin_project_screenshots.html",
        context={
            "project": project,
            "screenshots": get_project_screenshots(db, project.id),
            "error": error,
        },
        status_code=status_code,
    )


@router.get("/{project_id}/screenshots")
def admin_project_screenshots(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    project = get_project(db, project_id)
    if project is None:
        return RedirectResponse(url="/admin/projects", status_code=303)

    return render_gallery_manager(request, db, project)


@router.post("/{project_id}/screenshots/upload")
def admin_upload_project_screenshots(
    project_id: int,
    request: Request,
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    project = get_project(db, project_id)
    if project is None:
        return RedirectResponse(url="/admin/projects", status_code=303)

    uploads = [image for image in images if image.filename]
    if not uploads:
        return render_gallery_manager(
            request,
            db,
            project,
            error="Выберите хотя бы одно изображение.",
            status_code=400,
        )

    try:
        validated_uploads = [
            (upload, screenshot_storage.validate_screenshot(upload))
            for upload in uploads
        ]
    except screenshot_storage.InvalidScreenshotError as exc:
        return render_gallery_manager(
            request,
            db,
            project,
            error=str(exc),
            status_code=400,
        )

    last_sort_order = db.execute(
        select(func.max(ProjectScreenshot.sort_order)).where(
            ProjectScreenshot.project_id == project_id
        )
    ).scalar_one()
    next_sort_order = (last_sort_order or 0) + 1
    stored_paths: list[str] = []

    try:
        for offset, (upload, extension) in enumerate(validated_uploads):
            image_path = screenshot_storage.store_screenshot(upload, extension)
            stored_paths.append(image_path)
            db.add(
                ProjectScreenshot(
                    project_id=project_id,
                    image_path=image_path,
                    sort_order=next_sort_order + offset,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        for image_path in stored_paths:
            screenshot_storage.delete_screenshot_file(image_path)
        raise

    return RedirectResponse(
        url=f"/admin/projects/{project_id}/screenshots",
        status_code=303,
    )


@router.post("/{project_id}/screenshots/{screenshot_id}/edit")
def admin_edit_project_screenshot(
    project_id: int,
    screenshot_id: int,
    caption: str = Form(""),
    sort_order: int = Form(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    screenshot = db.execute(
        select(ProjectScreenshot).where(
            ProjectScreenshot.id == screenshot_id,
            ProjectScreenshot.project_id == project_id,
        )
    ).scalar_one_or_none()

    if screenshot is not None:
        screenshot.caption = caption.strip() or None
        screenshot.sort_order = sort_order
        db.commit()

    return RedirectResponse(
        url=f"/admin/projects/{project_id}/screenshots",
        status_code=303,
    )


@router.post("/{project_id}/screenshots/{screenshot_id}/delete")
def admin_delete_project_screenshot(
    project_id: int,
    screenshot_id: int,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    screenshot = db.execute(
        select(ProjectScreenshot).where(
            ProjectScreenshot.id == screenshot_id,
            ProjectScreenshot.project_id == project_id,
        )
    ).scalar_one_or_none()

    if screenshot is not None:
        image_path = screenshot.image_path
        db.delete(screenshot)
        db.commit()
        screenshot_storage.delete_screenshot_file(image_path)

    return RedirectResponse(
        url=f"/admin/projects/{project_id}/screenshots",
        status_code=303,
    )
