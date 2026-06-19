"""Service helpers for assembling content used by public and admin pages."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Profile, Project, SkillCategory


def get_homepage_content(db: Session) -> dict:
    """Build one shared context dictionary for homepage-like screens.

    Both the public homepage and the admin homepage render the same content
    blocks, so the data selection lives in one place to avoid duplication.
    """

    profile = db.execute(
        select(Profile)
        .options(selectinload(Profile.contacts))
        .order_by(Profile.id)
    ).scalars().first()

    skill_categories = db.execute(
        select(SkillCategory)
        .options(selectinload(SkillCategory.skills))
        .order_by(SkillCategory.sort_order, SkillCategory.id)
    ).scalars().all()

    featured_projects = db.execute(
        select(Project)
        .where(Project.is_featured.is_(True))
        .order_by(Project.sort_order, Project.id)
        # The homepage intentionally stays curated and shows only top-3 items.
        .limit(3)
    ).scalars().all()

    contacts = sorted(
        profile.contacts,
        key=lambda contact: (contact.sort_order, contact.id),
    ) if profile else []

    return {
        "profile": profile,
        "contacts": contacts,
        "skill_categories": skill_categories,
        "featured_projects": featured_projects,
    }
