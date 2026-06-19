"""Admin authentication routes: login and logout."""

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin-auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def admin_login_page(request: Request):
    if request.session.get("is_admin"):
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": None},
    )


@router.post("/login")
def admin_login(request: Request, password: str = Form(...)):
    # Password-only auth is enough because the project has one owner/admin.
    if password == settings.admin_password:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": "Неверный пароль"},
        status_code=400,
    )


@router.get("/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)
