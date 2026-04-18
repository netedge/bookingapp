from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from database import db
from auth import get_current_user
from models import CourtCreate

router = APIRouter(tags=["courts"])


@router.post("/courts")
async def create_court(court_data: CourtCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if user["role"] == "super_admin":
        if not court_data.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required for super_admin")
        tenant_id = court_data.tenant_id
    else:
        tenant_id = user["tenant_id"]

    court_doc = {
        "tenant_id": tenant_id,
        "venue_id": court_data.venue_id,
        "name": court_data.name,
        "sport_type": court_data.sport_type,
        "capacity": court_data.capacity,
        "indoor": court_data.indoor,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.courts.insert_one(court_doc)
    return {"id": str(result.inserted_id), **court_data.model_dump()}


@router.get("/courts")
async def get_courts(venue_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {"tenant_id": user.get("tenant_id")}
    if venue_id:
        query["venue_id"] = venue_id

    courts = []
    async for court in db.courts.find(query):
        court["id"] = str(court.pop("_id"))
        courts.append(court)
    return courts
