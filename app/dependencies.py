"""Reusable FastAPI dependencies shared between routers."""

from fastapi import Request
from fastapi.responses import RedirectResponse


def require_admin(request: Request) -> None | RedirectResponse:
    """Allow access only to authenticated admin sessions.

    Returning RedirectResponse instead of raising keeps the admin UX simple:
    unauthenticated users are sent straight to the login page.
    """

    if not request.session.get("is_admin"):
        return RedirectResponse(url="/admin/login", status_code=303)

    return None
