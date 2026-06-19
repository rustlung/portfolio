"""ORM models for skill categories and individual skills."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SkillCategory(Base):
    __tablename__ = "skill_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # When a category is removed from admin, its skills are removed too.
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("skill_categories.id"),
        nullable=False,
    )

    category: Mapped["SkillCategory"] = relationship(back_populates="skills")
