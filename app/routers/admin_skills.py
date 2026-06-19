"""Admin CRUD routes for skill categories and skills."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import require_admin
from app.models import Skill, SkillCategory

router = APIRouter(prefix="/admin", tags=["admin-skills"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/skills")
def admin_skills(
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    skill_categories = db.execute(
        select(SkillCategory)
        .options(selectinload(SkillCategory.skills))
        .order_by(SkillCategory.sort_order, SkillCategory.id)
    ).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="admin_skills.html",
        context={"skill_categories": skill_categories},
    )


@router.get("/skills/categories/create")
def admin_create_skill_category_page(
    request: Request,
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    return templates.TemplateResponse(
        request=request,
        name="admin_skill_category_form.html",
        context={
            "category": None,
            "form_title": "Добавить категорию навыков",
            "form_action": "/admin/skills/categories/create",
            "submit_label": "Создать",
        },
    )


@router.post("/skills/categories/create")
def admin_create_skill_category(
    request: Request,
    name: str = Form(...),
    sort_order: int = Form(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    category = SkillCategory(
        name=name,
        sort_order=sort_order,
    )

    db.add(category)
    db.commit()

    return RedirectResponse(url="/admin/skills", status_code=303)


@router.get("/skills/categories/{category_id}/edit")
def admin_edit_skill_category_page(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    category = db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    ).scalars().first()

    if category is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_skill_category_form.html",
        context={
            "category": category,
            "form_title": "Редактировать категорию навыков",
            "form_action": f"/admin/skills/categories/{category.id}/edit",
            "submit_label": "Сохранить",
        },
    )


@router.post("/skills/categories/{category_id}/edit")
def admin_edit_skill_category(
    category_id: int,
    request: Request,
    name: str = Form(...),
    sort_order: int = Form(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    category = db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    ).scalars().first()

    if category is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    category.name = name
    category.sort_order = sort_order

    db.commit()

    return RedirectResponse(url="/admin/skills", status_code=303)


@router.get("/skills/categories/{category_id}/delete")
def admin_delete_skill_category_page(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    category = db.execute(
        select(SkillCategory)
        .options(selectinload(SkillCategory.skills))
        .where(SkillCategory.id == category_id)
    ).scalars().first()

    if category is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_skill_category_delete.html",
        context={"category": category},
    )


@router.post("/skills/categories/{category_id}/delete")
def admin_delete_skill_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    # Because of cascade="all, delete-orphan", deleting a category
    # removes its nested skills as well.
    category = db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    ).scalars().first()

    if category is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    db.delete(category)
    db.commit()

    return RedirectResponse(url="/admin/skills", status_code=303)


@router.get("/skills/{category_id}/items/create")
def admin_create_skill_page(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    category = db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    ).scalars().first()

    if category is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_skill_form.html",
        context={
            "skill": None,
            "category": category,
            "form_title": f"Добавить навык в категорию {category.name}",
            "form_action": f"/admin/skills/{category.id}/items/create",
            "submit_label": "Создать",
        },
    )


@router.post("/skills/{category_id}/items/create")
def admin_create_skill(
    category_id: int,
    request: Request,
    name: str = Form(...),
    sort_order: int = Form(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    category = db.execute(
        select(SkillCategory).where(SkillCategory.id == category_id)
    ).scalars().first()

    if category is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    skill = Skill(
        name=name,
        sort_order=sort_order,
        category_id=category.id,
    )

    db.add(skill)
    db.commit()

    return RedirectResponse(url="/admin/skills", status_code=303)


@router.get("/skills/items/{skill_id}/edit")
def admin_edit_skill_page(
    skill_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    skill = db.execute(
        select(Skill).where(Skill.id == skill_id)
    ).scalars().first()

    if skill is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    category = db.execute(
        select(SkillCategory).where(SkillCategory.id == skill.category_id)
    ).scalars().first()

    return templates.TemplateResponse(
        request=request,
        name="admin_skill_form.html",
        context={
            "skill": skill,
            "category": category,
            "form_title": f"Редактировать навык: {skill.name}",
            "form_action": f"/admin/skills/items/{skill.id}/edit",
            "submit_label": "Сохранить",
        },
    )


@router.post("/skills/items/{skill_id}/edit")
def admin_edit_skill(
    skill_id: int,
    request: Request,
    name: str = Form(...),
    sort_order: int = Form(...),
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    skill = db.execute(
        select(Skill).where(Skill.id == skill_id)
    ).scalars().first()

    if skill is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    skill.name = name
    skill.sort_order = sort_order

    db.commit()

    return RedirectResponse(url="/admin/skills", status_code=303)


@router.get("/skills/items/{skill_id}/delete")
def admin_delete_skill_page(
    skill_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    skill = db.execute(
        select(Skill).where(Skill.id == skill_id)
    ).scalars().first()

    if skill is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    category = db.execute(
        select(SkillCategory).where(SkillCategory.id == skill.category_id)
    ).scalars().first()

    return templates.TemplateResponse(
        request=request,
        name="admin_skill_delete.html",
        context={
            "skill": skill,
            "category": category,
        },
    )


@router.post("/skills/items/{skill_id}/delete")
def admin_delete_skill(
    skill_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_check: None | RedirectResponse = Depends(require_admin),
):
    if admin_check:
        return admin_check

    skill = db.execute(
        select(Skill).where(Skill.id == skill_id)
    ).scalars().first()

    if skill is None:
        return RedirectResponse(url="/admin/skills", status_code=303)

    db.delete(skill)
    db.commit()

    return RedirectResponse(url="/admin/skills", status_code=303)
