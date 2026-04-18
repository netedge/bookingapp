from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from database import db
from auth import hash_password, get_current_user
from models import TenantCreate, TenantUpdate

router = APIRouter(tags=["tenants"])


@router.post("/tenants")
async def create_tenant(tenant_data: TenantCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can create tenants")

    existing = await db.tenants.find_one({"subdomain": tenant_data.subdomain})
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    tenant_doc = {
        "business_name": tenant_data.business_name,
        "subdomain": tenant_data.subdomain,
        "logo_url": None,
        "primary_color": "#059669",
        "timezone": tenant_data.timezone,
        "currency": tenant_data.currency,
        "created_at": datetime.now(timezone.utc),
        "status": "active",
    }
    tenant_result = await db.tenants.insert_one(tenant_doc)
    tenant_id = str(tenant_result.inserted_id)

    admin_doc = {
        "email": tenant_data.admin_email.lower(),
        "password_hash": hash_password(tenant_data.admin_password),
        "name": tenant_data.admin_name,
        "role": "tenant_admin",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(admin_doc)

    return {"id": tenant_id, "business_name": tenant_data.business_name, "subdomain": tenant_data.subdomain, "admin_email": tenant_data.admin_email}


@router.get("/tenants")
async def get_tenants(user: dict = Depends(get_current_user)):
    if user["role"] == "super_admin":
        tenants = []
        async for tenant in db.tenants.find({}):
            tenant["id"] = str(tenant.pop("_id"))
            tenants.append(tenant)
        return tenants
    elif user["role"] == "tenant_admin" and user.get("tenant_id"):
        tenant = await db.tenants.find_one({"_id": ObjectId(user["tenant_id"])})
        if tenant:
            tenant["id"] = str(tenant.pop("_id"))
            return [tenant]
    return []


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"_id": ObjectId(tenant_id)}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant["id"] = tenant_id
    return tenant


@router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, update_data: TenantUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if user["role"] == "tenant_admin" and user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Can only update own tenant")

    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if update_dict:
        await db.tenants.update_one({"_id": ObjectId(tenant_id)}, {"$set": update_dict})
    return {"message": "Tenant updated successfully"}


@router.put("/tenants/{tenant_id}/subscription")
async def update_tenant_subscription(tenant_id: str, plan_tier: str, user: dict = Depends(get_current_user)):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can update subscriptions")

    await db.tenants.update_one(
        {"_id": ObjectId(tenant_id)},
        {"$set": {"subscription_tier": plan_tier, "subscription_updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": "Subscription updated successfully"}


@router.get("/subscriptions/plans")
async def get_subscription_plans():
    return [
        {"plan_tier": "basic", "plan_name": "Basic", "monthly_price": 49.00, "features": {"max_venues": 1, "max_courts": 5, "max_bookings_per_month": 100, "analytics": False, "custom_domain": False, "email_notifications": True, "priority_support": False}},
        {"plan_tier": "pro", "plan_name": "Professional", "monthly_price": 149.00, "features": {"max_venues": 5, "max_courts": 25, "max_bookings_per_month": 500, "analytics": True, "custom_domain": True, "email_notifications": True, "priority_support": True}},
        {"plan_tier": "enterprise", "plan_name": "Enterprise", "monthly_price": 499.00, "features": {"max_venues": "unlimited", "max_courts": "unlimited", "max_bookings_per_month": "unlimited", "analytics": True, "custom_domain": True, "email_notifications": True, "priority_support": True, "white_label": True, "api_access": True}},
    ]
