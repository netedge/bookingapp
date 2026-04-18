import os
import io
import base64

import qrcode
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from database import db
from auth import get_current_user
from models import PricingRuleCreate
from datetime import datetime, timezone
from typing import Optional
from fastapi import Query

router = APIRouter(tags=["qr-pricing"])


def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"


@router.get("/qr-code/{venue_id}")
async def get_venue_qr_code(venue_id: str, user: dict = Depends(get_current_user)):
    venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    tenant = await db.tenants.find_one({"_id": ObjectId(venue["tenant_id"])})
    app_domain = os.environ.get("APP_DOMAIN", "spancle.com")
    booking_url = f"https://{tenant['subdomain']}.{app_domain}/book/{venue_id}"
    return {"qr_code": generate_qr_code(booking_url), "booking_url": booking_url}


@router.post("/pricing")
async def create_pricing_rule(pricing_data: PricingRuleCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if user["role"] == "super_admin":
        if not pricing_data.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required for super_admin")
        tenant_id = pricing_data.tenant_id
    else:
        tenant_id = user["tenant_id"]

    pricing_doc = {
        "tenant_id": tenant_id, "court_id": pricing_data.court_id,
        "rule_type": pricing_data.rule_type, "price": pricing_data.price,
        "start_time": pricing_data.start_time, "end_time": pricing_data.end_time,
        "days_of_week": pricing_data.days_of_week, "created_at": datetime.now(timezone.utc),
    }
    result = await db.pricing_rules.insert_one(pricing_doc)
    return {"id": str(result.inserted_id), **pricing_data.model_dump()}


@router.get("/pricing")
async def get_pricing_rules(court_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {"tenant_id": user.get("tenant_id")}
    if court_id:
        query["court_id"] = court_id

    rules = []
    async for rule in db.pricing_rules.find(query):
        rule["id"] = str(rule.pop("_id"))
        rules.append(rule)
    return rules
