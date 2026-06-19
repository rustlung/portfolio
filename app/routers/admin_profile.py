"""Admin routes for the admin homepage and profile editing."""

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4

from app.database import get_db
from app.dependencies import require_admin
from app.models import Profile
from app.services.site_content import get_homepage_content

router = APIRouter(prefix="/admin", tags=["admin-profile"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def admin_index(
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    # Admin homepage reuses the same content as the public homepage,
    # but renders extra management controls in the template.
    context = get_homepage_content(db)

    return templates.TemplateResponse(
        request=request,
        name="admin_home.html",
        context=context,
    )


@router.get("/profile/edit")
def admin_edit_profile_page(
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    profile = db.execute(
        select(Profile).order_by(Profile.id)
    ).scalars().first()

    return templates.TemplateResponse(
        request=request,
        name="admin_profile_edit.html",
        context={"profile": profile},
    )


@router.post("/profile/edit")
def admin_edit_profile(
    request: Request,
    full_name: str = Form(...),
    title: str = Form(...),
    subtitle: str = Form(...),
    about_text: str = Form(...),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    # The project assumes a single Profile row for the site owner.
    profile = db.execute(
        select(Profile).order_by(Profile.id)
    ).scalars().first()

    if profile is None:
        profile = Profile(
            full_name=full_name,
            title=title,
            subtitle=subtitle,
            about_text=about_text,
            photo_path=None,
        )
        db.add(profile)
    else:
        profile.full_name = full_name
        profile.title = title
        profile.subtitle = subtitle
        profile.about_text = about_text
    
    if photo and photo.filename:
        uploads_dir = Path("app/static/uploads/profile")
        uploads_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(photo.filename).suffix.lower()
        safe_extension = extension if extension in {".png", ".jpg", ".jpeg", ".webp"} else ".png"

        filename = f"profile_{uuid4().hex}{safe_extension}"
        file_path = uploads_dir / filename

        with file_path.open("wb") as buffer:
            buffer.write(photo.file.read())

        profile.photo_path = f"/static/uploads/profile/{filename}"

    db.commit()

    return RedirectResponse(url="/admin", status_code=303)
