"""Admin CRUD routes for contact links shown on the homepage."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Contact, Profile

router = APIRouter(prefix="/admin", tags=["admin-contacts"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/contacts")
def admin_contacts(
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    contacts = db.execute(
        select(Contact).order_by(Contact.sort_order, Contact.id)
    ).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="admin_contacts.html",
        context={"contacts": contacts},
    )


@router.get("/contacts/create")
def admin_create_contact_page(
    request: Request,
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    return templates.TemplateResponse(
        request=request,
        name="admin_contact_form.html",
        context={
            "contact": None,
            "form_title": "Добавить контакт",
            "form_action": "/admin/contacts/create",
            "submit_label": "Создать",
        },
    )


@router.post("/contacts/create")
def admin_create_contact(
    request: Request,
    type: str = Form(...),
    label: str = Form(...),
    value: str = Form(...),
    url: str = Form(...),
    sort_order: int = Form(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    # New contacts are always attached to the single site profile.
    profile = db.execute(
        select(Profile).order_by(Profile.id)
    ).scalars().first()

    if profile is None:
        return RedirectResponse(url="/admin/profile/edit", status_code=303)

    contact = Contact(
        type=type,
        label=label,
        value=value,
        url=url,
        sort_order=sort_order,
        profile_id=profile.id,
    )

    db.add(contact)
    db.commit()

    return RedirectResponse(url="/admin/contacts", status_code=303)


@router.get("/contacts/{contact_id}/edit")
def admin_edit_contact_page(
    contact_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    contact = db.execute(
        select(Contact).where(Contact.id == contact_id)
    ).scalars().first()

    if contact is None:
        return RedirectResponse(url="/admin/contacts", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_contact_form.html",
        context={
            "contact": contact,
            "form_title": "Редактировать контакт",
            "form_action": f"/admin/contacts/{contact.id}/edit",
            "submit_label": "Сохранить",
        },
    )


@router.post("/contacts/{contact_id}/edit")
def admin_edit_contact(
    contact_id: int,
    request: Request,
    type: str = Form(...),
    label: str = Form(...),
    value: str = Form(...),
    url: str = Form(...),
    sort_order: int = Form(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    contact = db.execute(
        select(Contact).where(Contact.id == contact_id)
    ).scalars().first()

    if contact is None:
        return RedirectResponse(url="/admin/contacts", status_code=303)

    contact.type = type
    contact.label = label
    contact.value = value
    contact.url = url
    contact.sort_order = sort_order

    db.commit()

    return RedirectResponse(url="/admin/contacts", status_code=303)


@router.get("/contacts/{contact_id}/delete")
def admin_delete_contact_page(
    contact_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    contact = db.execute(
        select(Contact).where(Contact.id == contact_id)
    ).scalars().first()

    if contact is None:
        return RedirectResponse(url="/admin/contacts", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_contact_delete.html",
        context={"contact": contact},
    )


@router.post("/contacts/{contact_id}/delete")
def admin_delete_contact(
    contact_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    contact = db.execute(
        select(Contact).where(Contact.id == contact_id)
    ).scalars().first()

    if contact is None:
        return RedirectResponse(url="/admin/contacts", status_code=303)

    db.delete(contact)
    db.commit()

    return RedirectResponse(url="/admin/contacts", status_code=303)
