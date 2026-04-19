from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from database import db, client
from auth import hash_password, verify_password

from routes.auth import router as auth_router
from routes.tenants import router as tenants_router
from routes.venues import router as venues_router
from routes.courts import router as courts_router
from routes.bookings import router as bookings_router
from routes.customers import router as customers_router
from routes.payments import router as payments_router
from routes.analytics import router as analytics_router
from routes.public import router as public_router
from routes.qr import router as qr_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_admin() -> None:
    admin_email: str = os.environ.get("ADMIN_EMAIL", "admin@spancle.com")
    admin_password: str = os.environ.get("ADMIN_PASSWORD", "admin123")

    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Super Admin",
            "role": "super_admin",
            "tenant_id": None,
            "created_at": datetime.now(timezone.utc),
        })
        logger.info(f"Super admin created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )
        logger.info("Super admin password updated")


@asynccontextmanager
async def lifespan(app):
    # Startup
    await db.users.create_index("email", unique=True)
    await db.tenants.create_index("subdomain", unique=True)
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.login_attempts.create_index("identifier")
    await seed_admin()
    logger.info("Spancle backend started")
    yield
    # Shutdown
    client.close()
    logger.info("Spancle backend shut down")


app = FastAPI(lifespan=lifespan)

# CORS - must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Main API router
api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(tenants_router)
api_router.include_router(venues_router)
api_router.include_router(courts_router)
api_router.include_router(bookings_router)
api_router.include_router(customers_router)
api_router.include_router(payments_router)
api_router.include_router(analytics_router)
api_router.include_router(public_router)
api_router.include_router(qr_router)
app.include_router(api_router)
