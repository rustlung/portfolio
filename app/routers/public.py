"""Public-facing routes rendered for portfolio visitors."""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.services.site_content import get_homepage_content
from app.database import get_db
from app.models import Profile, Project, SkillCategory


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def read_home(request: Request, db: Session = Depends(get_db)):
    # Public homepage and admin homepage intentionally share one content service.
    context = get_homepage_content(db)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=context,
    )


@router.get("/projects")
def read_projects(request: Request, db: Session = Depends(get_db)):
    projects = db.execute(
        select(Project)
        .order_by(Project.sort_order, Project.id)
    ).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={
            "projects": projects,
        },
    )


@router.get("/projects/{slug}")
def read_project_detail(
    slug: str,
    request: Request,
    db: Session = Depends(get_db)
):
    project = db.execute(
        select(Project).where(Project.slug == slug)
    ).scalars().first()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return templates.TemplateResponse(
        request=request,
        name="project_detail.html",
        context={
            "project": project,
        },
    )
