from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, Response

from database import db
from auth import get_current_user

router = APIRouter(tags=["analytics"])


@router.get("/analytics/dashboard")
async def get_analytics(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")

    if user["role"] == "super_admin":
        total_bookings = await db.bookings.count_documents({})
        total_venues = await db.venues.count_documents({})
        total_customers = await db.customers.count_documents({})
        revenue_pipeline = [{"$match": {"payment_status": "paid"}}, {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}]
    else:
        total_bookings = await db.bookings.count_documents({"tenant_id": tenant_id}) if tenant_id else 0
        total_venues = await db.venues.count_documents({"tenant_id": tenant_id}) if tenant_id else 0
        total_customers = await db.customers.count_documents({"tenant_id": tenant_id}) if tenant_id else 0
        revenue_pipeline = [{"$match": {"payment_status": "paid", "tenant_id": tenant_id}}, {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}] if tenant_id else []

    total_revenue = 0
    if revenue_pipeline:
        result = await db.bookings.aggregate(revenue_pipeline).to_list(1)
        total_revenue = result[0]["total"] if result else 0

    return {"total_bookings": total_bookings, "total_venues": total_venues, "total_customers": total_customers, "total_revenue": total_revenue}


@router.get("/analytics/revenue-trend")
async def get_revenue_trend(days: int = 30, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    match_stage = {"payment_status": "paid", "created_at": {"$gte": start_date, "$lte": end_date}}
    if user["role"] != "super_admin" and tenant_id:
        match_stage["tenant_id"] = tenant_id

    pipeline = [{"$match": match_stage}, {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "revenue": {"$sum": "$total_price"}, "bookings": {"$sum": 1}}}, {"$sort": {"_id": 1}}]
    result = await db.bookings.aggregate(pipeline).to_list(100)

    return {"dates": [item["_id"] for item in result], "revenue": [item["revenue"] for item in result], "bookings": [item["bookings"] for item in result]}


@router.get("/analytics/court-occupancy")
async def get_court_occupancy(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    court_query = {"tenant_id": tenant_id} if tenant_id and user["role"] != "super_admin" else {}
    courts = await db.courts.find(court_query).to_list(100)
    if not courts:
        return []

    court_ids = [str(court["_id"]) for court in courts]
    booking_counts = await db.bookings.aggregate([
        {"$match": {"court_id": {"$in": court_ids}, "status": {"$in": ["confirmed", "completed"]}}},
        {"$group": {"_id": "$court_id", "count": {"$sum": 1}}},
    ]).to_list(100)
    booking_map = {item["_id"]: item["count"] for item in booking_counts}

    data = []
    for court in courts:
        cid = str(court["_id"])
        count = booking_map.get(cid, 0)
        data.append({"court_name": court.get("name"), "sport_type": court.get("sport_type"), "bookings": count, "occupancy_rate": min(count / 30 * 100, 100)})

    return sorted(data, key=lambda x: x["occupancy_rate"], reverse=True)


@router.get("/export/bookings")
async def export_bookings_csv(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    query = {"tenant_id": tenant_id} if tenant_id and user["role"] != "super_admin" else {}
    bookings = await db.bookings.find(query).sort("date", -1).to_list(1000)

    csv_data = "Booking ID,Customer Name,Customer Email,Date,Start Time,End Time,Court ID,Total Price,Status,Payment Status\n"
    for b in bookings:
        csv_data += f"\"{str(b['_id'])}\",\"{b.get('customer_name', '')}\",\"{b.get('customer_email', '')}\",\"{b.get('date', '')}\",\"{b.get('start_time', '')}\",\"{b.get('end_time', '')}\",\"{b.get('court_id', '')}\",{b.get('total_price', 0)},\"{b.get('status', '')}\",\"{b.get('payment_status', '')}\"\n"

    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=bookings_{datetime.now().strftime('%Y%m%d')}.csv"})


@router.get("/export/analytics")
async def export_analytics_csv(days: int = 30, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    match_stage = {"payment_status": "paid", "created_at": {"$gte": start_date, "$lte": end_date}}
    if user["role"] != "super_admin" and tenant_id:
        match_stage["tenant_id"] = tenant_id

    pipeline = [{"$match": match_stage}, {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "revenue": {"$sum": "$total_price"}, "bookings": {"$sum": 1}}}, {"$sort": {"_id": 1}}]
    result = await db.bookings.aggregate(pipeline).to_list(1000)

    csv_data = "Date,Revenue,Bookings\n"
    for item in result:
        csv_data += f"\"{item['_id']}\",{item['revenue']},{item['bookings']}\n"

    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d')}.csv"})
