from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query

from database import db
from auth import get_current_user
from models import VenueCreate

router = APIRouter(tags=["venues"])


def resolve_tenant_id(user: dict, provided_tenant_id: Optional[str]) -> str:
    if user["role"] == "super_admin":
        if not provided_tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required for super_admin")
        return provided_tenant_id
    return user["tenant_id"]


@router.post("/venues")
async def create_venue(venue_data: VenueCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    tenant_id = resolve_tenant_id(user, venue_data.tenant_id)
    venue_doc = {
        "tenant_id": tenant_id,
        "name": venue_data.name,
        "description": venue_data.description,
        "address": venue_data.address,
        "image_url": venue_data.image_url or "https://images.unsplash.com/photo-1765124540460-b884e248ac2b",
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.venues.insert_one(venue_doc)
    return {"id": str(result.inserted_id), **venue_data.model_dump()}


@router.get("/venues")
async def get_venues(tenant_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {}
    if user["role"] == "super_admin":
        if tenant_id:
            query["tenant_id"] = tenant_id
    else:
        query["tenant_id"] = user["tenant_id"]

    venues = []
    async for venue in db.venues.find(query):
        venue["id"] = str(venue.pop("_id"))
        venues.append(venue)
    return venues


@router.post("/bulk-import/venues")
async def bulk_import_venues(venues_data: List[VenueCreate], user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    imported = []
    errors = []
    for idx, venue_data in enumerate(venues_data):
        try:
            tenant_id = resolve_tenant_id(user, venue_data.tenant_id)
            venue_doc = {
                "tenant_id": tenant_id,
                "name": venue_data.name,
                "description": venue_data.description,
                "address": venue_data.address,
                "image_url": venue_data.image_url or "https://images.unsplash.com/photo-1765124540460-b884e248ac2b",
                "created_at": datetime.now(timezone.utc),
            }
            result = await db.venues.insert_one(venue_doc)
            imported.append({"index": idx, "id": str(result.inserted_id), "name": venue_data.name})
        except HTTPException as he:
            errors.append({"index": idx, "error": he.detail})
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    return {"imported_count": len(imported), "error_count": len(errors), "imported": imported, "errors": errors}
