import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId

from database import db
from auth import get_current_user
from models import BookingCreate, RecurringBookingCreate
from email_service import send_booking_confirmation_email, send_booking_cancellation_email

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bookings"])


def generate_recurrence_dates(start_date_str: str, end_date_str: str, days_of_week: list) -> list:
    from datetime import datetime as dt
    start = dt.strptime(start_date_str, "%Y-%m-%d")
    end = dt.strptime(end_date_str, "%Y-%m-%d")
    dates = []
    current = start
    while current <= end:
        if current.weekday() in days_of_week:
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def build_recurring_doc(data: RecurringBookingCreate, date_str: str) -> dict:
    return {
        "court_id": data.court_id,
        "customer_email": data.customer_email,
        "customer_name": data.customer_name,
        "customer_phone": data.customer_phone,
        "date": date_str,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "total_price": data.total_price,
        "status": "confirmed",
        "payment_status": "pending",
        "recurring": True,
        "created_at": datetime.now(timezone.utc),
    }


@router.post("/bookings")
async def create_booking(booking_data: BookingCreate):
    existing = await db.bookings.find_one({
        "court_id": booking_data.court_id,
        "date": booking_data.date,
        "status": {"$in": ["pending", "confirmed"]},
        "$or": [{"start_time": {"$lt": booking_data.end_time}, "end_time": {"$gt": booking_data.start_time}}],
    })
    if existing:
        raise HTTPException(status_code=400, detail="Slot already booked")

    booking_doc = {**booking_data.model_dump(), "status": "confirmed", "created_at": datetime.now(timezone.utc), "payment_status": "pending"}
    result = await db.bookings.insert_one(booking_doc)
    booking_id = str(result.inserted_id)

    try:
        court = await db.courts.find_one({"_id": ObjectId(booking_data.court_id)})
        if court:
            venue = await db.venues.find_one({"_id": ObjectId(court.get("venue_id"))})
            if venue:
                await send_booking_confirmation_email(booking_doc, booking_data.customer_email, venue.get("name", "Venue"), court.get("name", "Court"))
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {e}")

    return {"id": booking_id, **booking_data.model_dump(), "status": "confirmed"}


@router.get("/bookings")
async def get_bookings(court_id: Optional[str] = Query(None), date: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {}
    if court_id:
        query["court_id"] = court_id
    if date:
        query["date"] = date

    bookings = []
    async for booking in db.bookings.find(query).sort("date", -1):
        booking["id"] = str(booking.pop("_id"))
        bookings.append(booking)
    return bookings


@router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, user: dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    await db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": "cancelled"}})

    try:
        court = await db.courts.find_one({"_id": ObjectId(booking.get("court_id"))})
        if court:
            venue = await db.venues.find_one({"_id": ObjectId(court.get("venue_id"))})
            if venue:
                await send_booking_cancellation_email(booking, booking.get("customer_email"), venue.get("name", "Venue"))
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")

    return {"message": "Booking cancelled successfully"}


@router.post("/bookings/recurring")
async def create_recurring_booking(booking_data: RecurringBookingCreate, user: dict = Depends(get_current_user)):
    dates = generate_recurrence_dates(booking_data.start_date, booking_data.end_date, booking_data.days_of_week)

    created_bookings = []
    conflicts = []
    for date_str in dates:
        existing = await db.bookings.find_one({
            "court_id": booking_data.court_id,
            "date": date_str,
            "status": {"$in": ["pending", "confirmed"]},
            "$or": [{"start_time": {"$lt": booking_data.end_time}, "end_time": {"$gt": booking_data.start_time}}],
        })
        if not existing:
            doc = build_recurring_doc(booking_data, date_str)
            result = await db.bookings.insert_one(doc)
            created_bookings.append({"date": date_str, "id": str(result.inserted_id)})
        else:
            conflicts.append(date_str)

    return {"created_count": len(created_bookings), "conflict_count": len(conflicts), "created_bookings": created_bookings, "conflicts": conflicts}
