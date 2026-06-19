"""Initial data for a brand-new local database.

The seed stays intentionally generic so the public repository does not expose
personal data. Replace the placeholder content through the admin panel after
the first launch.
"""

from sqlalchemy.orm import Session

from app.models import Profile


def seed_database(db: Session) -> None:
    # Profile is used as the signal that the initial dataset already exists.
    existing_profile = db.query(Profile).first()
    if existing_profile is not None:
        return

    # One placeholder profile record is enough to initialize the single-profile site.
    profile = Profile(
        full_name="Your Name",
        title="Your Role",
        subtitle="Your Stack • Your Focus • Your Direction",
        about_text=(
            "Replace this placeholder text through the admin panel. "
            "Use it for a short professional summary, key technologies and "
            "the types of products or problems you work with."
        ),
        photo_path=None,
    )

    # Everything else is intentionally left empty and should be created through admin.
    db.add(profile)
    db.commit()
