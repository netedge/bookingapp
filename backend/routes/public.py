from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId

from database import db
from models import BookingCreate

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/tenant/{subdomain}")
async def get_tenant_by_subdomain(subdomain: str):
    tenant = await db.tenants.find_one({"subdomain": subdomain})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant_id = str(tenant["_id"])
    venues = []
    async for v in db.venues.find({"tenant_id": tenant_id}):
        venues.append({"id": str(v["_id"]), "name": v.get("name", ""), "description": v.get("description", ""), "address": v.get("address", ""), "image_url": v.get("image_url", "")})

    return {"tenant_id": tenant_id, "business_name": tenant.get("business_name", ""), "subdomain": tenant.get("subdomain", ""), "subscription_tier": tenant.get("subscription_tier", "free"), "venues": venues}


@router.get("/venue/{venue_id}")
async def get_public_venue(venue_id: str):
    venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    courts = []
    async for c in db.courts.find({"venue_id": venue_id}):
        courts.append({"id": str(c["_id"]), "name": c.get("name", ""), "sport_type": c.get("sport_type", ""), "venue_id": c.get("venue_id", "")})

    return {"id": str(venue["_id"]), "name": venue.get("name", ""), "description": venue.get("description", ""), "address": venue.get("address", ""), "image_url": venue.get("image_url", ""), "tenant_id": venue.get("tenant_id", ""), "courts": courts}


@router.get("/courts/{venue_id}")
async def get_public_courts(venue_id: str):
    courts = []
    async for c in db.courts.find({"venue_id": venue_id}):
        courts.append({"id": str(c["_id"]), "name": c.get("name", ""), "sport_type": c.get("sport_type", ""), "venue_id": c.get("venue_id", "")})
    return courts


@router.get("/bookings")
async def get_public_bookings(court_id: str = Query(...), date: str = Query(...)):
    bookings = await db.bookings.find({"court_id": court_id, "date": date, "status": {"$ne": "cancelled"}}, {"_id": 0}).to_list(100)
    return bookings


@router.post("/bookings")
async def create_public_booking(booking: BookingCreate):
    booking_doc = {
        "court_id": booking.court_id, "customer_name": booking.customer_name,
        "customer_email": booking.customer_email, "customer_phone": booking.customer_phone,
        "date": booking.date, "start_time": booking.start_time, "end_time": booking.end_time,
        "total_price": booking.total_price, "status": "pending", "payment_status": "pending",
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.bookings.insert_one(booking_doc)
    return {"id": str(result.inserted_id), "status": "pending", "message": "Booking created successfully"}
