import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request, Response, Depends

from database import db
from auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    set_auth_cookies, get_current_user,
)
from config import FRONTEND_URL
from models import LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest, TenantRegisterRequest
from email_service import send_password_reset_email
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])


async def verify_credentials(email: str, password: str, identifier: str) -> dict:
    """Verify user credentials with brute force protection (5-attempt lockout)."""
    attempt_record = await db.login_attempts.find_one({"identifier": identifier})
    if attempt_record:
        locked_until = attempt_record.get("locked_until")
        if locked_until:
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > datetime.now(timezone.utc):
                raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        current_attempts = (attempt_record.get("attempts", 0) if attempt_record else 0) + 1
        update_fields: Dict[str, Any] = {"last_attempt": datetime.now(timezone.utc)}
        if current_attempts >= 5:
            update_fields["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"attempts": 1}, "$set": update_fields},
            upsert=True,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await db.login_attempts.delete_one({"identifier": identifier})
    return user


@router.post("/register")
async def register(request: RegisterRequest, response: Response):
    email = request.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = {
        "email": email,
        "password_hash": hash_password(request.password),
        "name": request.name,
        "role": request.role,
        "tenant_id": request.tenant_id,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)

    access_token = create_access_token(user_id, email, request.role)
    refresh_token = create_refresh_token(user_id)
    set_auth_cookies(response, access_token, refresh_token)

    return {"id": user_id, "email": email, "name": request.name, "role": request.role, "tenant_id": request.tenant_id}


@router.post("/register-tenant")
async def register_tenant(request: TenantRegisterRequest, response: Response):
    """Self-serve tenant registration: creates tenant + tenant_admin user in one step."""
    email = request.email.lower()
    subdomain = request.subdomain.lower().strip()

    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_tenant = await db.tenants.find_one({"subdomain": subdomain})
    if existing_tenant:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    tenant_doc = {
        "business_name": request.business_name,
        "subdomain": subdomain,
        "logo_url": None,
        "primary_color": "#059669",
        "timezone": "UTC",
        "currency": "USD",
        "created_at": datetime.now(timezone.utc),
        "status": "active",
    }
    tenant_result = await db.tenants.insert_one(tenant_doc)
    tenant_id = str(tenant_result.inserted_id)

    user_data = {
        "email": email,
        "password_hash": hash_password(request.password),
        "name": request.name,
        "role": "tenant_admin",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)

    access_token = create_access_token(user_id, email, "tenant_admin")
    refresh_token = create_refresh_token(user_id)
    set_auth_cookies(response, access_token, refresh_token)

    return {"id": user_id, "email": email, "name": request.name, "role": "tenant_admin", "tenant_id": tenant_id}


@router.post("/login")
async def login(request: LoginRequest, response: Response, http_request: Request):
    email = request.email.lower()
    identifier = f"{http_request.client.host}:{email}"

    user = await verify_credentials(email, request.password, identifier)

    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email, user["role"])
    refresh_token = create_refresh_token(user_id)
    set_auth_cookies(response, access_token, refresh_token)

    return {"id": user_id, "email": email, "name": user["name"], "role": user["role"], "tenant_id": user.get("tenant_id")}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    email = request.email.lower()
    user = await db.users.find_one({"email": email})

    if not user:
        return {"message": "If an account with that email exists, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    await db.password_reset_tokens.insert_one({
        "token": token,
        "user_id": str(user["_id"]),
        "email": email,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False,
        "created_at": datetime.now(timezone.utc),
    })

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    await send_password_reset_email(email, user.get("name", "there"), reset_link)

    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    record = await db.password_reset_tokens.find_one({
        "token": request.token,
        "used": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    })
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    await db.users.update_one(
        {"_id": ObjectId(record["user_id"])},
        {"$set": {"password_hash": hash_password(request.new_password)}},
    )
    await db.password_reset_tokens.update_one(
        {"token": request.token},
        {"$set": {"used": True}},
    )
    return {"message": "Password has been reset successfully"}
