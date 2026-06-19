"""Application entry point.

This module wires together the whole app:
- loads settings and middleware;
- initializes the database on startup;
- mounts static files;
- connects public and admin routers.
"""

from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine
from app.routers.admin_auth import router as admin_auth_router
from app.routers.public import router as public_router
from app.routers.admin_profile import router as admin_profile_router
from app.routers.admin_contacts import router as admin_contacts_router
from app.routers.admin_skills import router as admin_skills_router
from app.routers.admin_projects import router as admin_projects_router

from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and populate the empty database once at startup.
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        seed_database(db)
    yield


app = FastAPI(
    title="Portfolio CMS",
    lifespan=lifespan,
)

# Session middleware is used for the password-protected admin area.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key
)

# Public router and admin routers are split by responsibility to keep modules small.
app.include_router(public_router)
app.include_router(admin_auth_router)
app.include_router(admin_profile_router)
app.include_router(admin_contacts_router)
app.include_router(admin_skills_router)
app.include_router(admin_projects_router)

# Static files contain the site CSS and image assets used by templates.
app.mount("/static", StaticFiles(directory="app/static"), name="static")
