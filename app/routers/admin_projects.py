"""Admin CRUD routes for portfolio projects."""

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4

from app.database import get_db
from app.dependencies import require_admin
from app.models import Project

router = APIRouter(prefix="/admin", tags=["admin-projects"])
templates = Jinja2Templates(directory="app/templates")


def get_featured_projects_count(db: Session) -> int:
    """Return how many projects are currently marked for the homepage top block."""

    return db.execute(
        select(func.count()).select_from(Project).where(Project.is_featured.is_(True))
    ).scalar_one()


@router.get("/projects")
def admin_projects(
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    projects = db.execute(
        select(Project).order_by(Project.sort_order, Project.id)
    ).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="admin_projects.html",
        context={"projects": projects},
    )


@router.get("/projects/create")
def admin_create_project_page(
    request: Request,
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    return templates.TemplateResponse(
        request=request,
        name="admin_project_form.html",
        context={
            "project": None,
            "form_title": "Добавить проект",
            "form_action": "/admin/projects/create",
            "submit_label": "Создать",
        },
    )


@router.post("/projects/create")
def admin_create_project(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    short_description: str = Form(...),
    full_description: str = Form(...),
    problem: str = Form(...),
    features: str = Form(...),
    result: str = Form(...),
    practical_use: str = Form(...),
    technologies: str = Form(...),
    github_url: str = Form(""),
    demo_url: str = Form(""),
    image: UploadFile | None = File(None),
    sort_order: int = Form(...),
    is_featured: bool = Form(False),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    # The homepage is intentionally curated and must not show more than 3
    # featured projects at the same time.
    if is_featured and get_featured_projects_count(db) >= 3:
        form_project = {
            "title": title,
            "slug": slug,
            "short_description": short_description,
            "full_description": full_description,
            "problem": problem,
            "features": features,
            "result": result,
            "practical_use": practical_use,
            "technologies": technologies,
            "github_url": github_url,
            "demo_url": demo_url,
            "sort_order": sort_order,
            "is_featured": is_featured,
        }

        return templates.TemplateResponse(
            request=request,
            name="admin_project_form.html",
            context={
                "project": form_project,
                "form_title": "Добавить проект",
                "form_action": "/admin/projects/create",
                "submit_label": "Создать",
                "error": "На главной странице может быть не более 3 избранных проектов.",
            },
            status_code=400,
        )

    image_path = None

    if image and image.filename:
        uploads_dir = Path("app/static/uploads/projects")
        uploads_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(image.filename).suffix.lower()
        safe_extension = extension if extension in {".png", ".jpg", ".jpeg", ".webp"} else ".png"

        filename = f"project_{uuid4().hex}{safe_extension}"
        file_path = uploads_dir / filename

        with file_path.open("wb") as buffer:
            buffer.write(image.file.read())

        image_path = f"/static/uploads/projects/{filename}"

    project = Project(
        title=title,
        slug=slug,
        short_description=short_description,
        full_description=full_description,
        problem=problem,
        features=features,
        result=result,
        practical_use=practical_use,
        technologies=technologies,
        github_url=github_url or None,
        demo_url=demo_url or None,
        image_path=image_path,
        sort_order=sort_order,
        is_featured=is_featured,
    )

    db.add(project)
    db.commit()

    return RedirectResponse(url="/admin/projects", status_code=303)


@router.get("/projects/{project_id}/edit")
def admin_edit_project_page(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    project = db.execute(
        select(Project).where(Project.id == project_id)
    ).scalars().first()

    if project is None:
        return RedirectResponse(url="/admin/projects", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_project_form.html",
        context={
            "project": project,
            "form_title": f"Редактировать проект: {project.title}",
            "form_action": f"/admin/projects/{project.id}/edit",
            "submit_label": "Сохранить",
        },
    )


@router.post("/projects/{project_id}/edit")
def admin_edit_project(
    project_id: int,
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    short_description: str = Form(...),
    full_description: str = Form(...),
    problem: str = Form(...),
    features: str = Form(...),
    result: str = Form(...),
    practical_use: str = Form(...),
    technologies: str = Form(...),
    github_url: str = Form(""),
    demo_url: str = Form(""),
    image: UploadFile | None = File(None),
    sort_order: int = Form(...),
    is_featured: bool = Form(False),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    project = db.execute(
        select(Project).where(Project.id == project_id)
    ).scalars().first()

    if project is None:
        return RedirectResponse(url="/admin/projects", status_code=303)

    # Existing featured projects may stay featured, but a non-featured project
    # cannot become the fourth featured card.
    if is_featured and not project.is_featured and get_featured_projects_count(db) >= 3:
        form_project = {
            "id": project.id,
            "title": title,
            "slug": slug,
            "short_description": short_description,
            "full_description": full_description,
            "problem": problem,
            "features": features,
            "result": result,
            "practical_use": practical_use,
            "technologies": technologies,
            "github_url": github_url,
            "demo_url": demo_url,
            "sort_order": sort_order,
            "is_featured": is_featured,
        }

        return templates.TemplateResponse(
            request=request,
            name="admin_project_form.html",
            context={
                "project": form_project,
                "form_title": f"Редактировать проект: {project.title}",
                "form_action": f"/admin/projects/{project.id}/edit",
                "submit_label": "Сохранить",
                "error": "На главной странице может быть не более 3 избранных проектов.",
            },
            status_code=400,
        )

    project.title = title
    project.slug = slug
    project.short_description = short_description
    project.full_description = full_description
    project.problem = problem
    project.features = features
    project.result = result
    project.practical_use = practical_use
    project.technologies = technologies
    project.github_url = github_url or None
    project.demo_url = demo_url or None
    project.sort_order = sort_order
    project.is_featured = is_featured

    if image and image.filename:
        uploads_dir = Path("app/static/uploads/projects")
        uploads_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(image.filename).suffix.lower()
        safe_extension = extension if extension in {".png", ".jpg", ".jpeg", ".webp"} else ".png"

        filename = f"project_{uuid4().hex}{safe_extension}"
        file_path = uploads_dir / filename

        with file_path.open("wb") as buffer:
            buffer.write(image.file.read())

        project.image_path = f"/static/uploads/projects/{filename}"

    db.commit()

    return RedirectResponse(url="/admin/projects", status_code=303)


@router.get("/projects/{project_id}/delete")
def admin_delete_project_page(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    project = db.execute(
        select(Project).where(Project.id == project_id)
    ).scalars().first()

    if project is None:
        return RedirectResponse(url="/admin/projects", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_project_delete.html",
        context={"project": project},
    )


@router.post("/projects/{project_id}/delete")
def admin_delete_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    project = db.execute(
        select(Project).where(Project.id == project_id)
    ).scalars().first()

    if project is None:
        return RedirectResponse(url="/admin/projects", status_code=303)

    db.delete(project)
    db.commit()

    return RedirectResponse(url="/admin/projects", status_code=303)
