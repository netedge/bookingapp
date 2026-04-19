from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from typing import Optional

from database import db
from auth import get_current_user
from models import CustomerCreate

router = APIRouter(tags=["customers"])


@router.post("/customers")
async def create_customer(customer_data: CustomerCreate, user: dict = Depends(get_current_user)):
    customer_doc = {**customer_data.model_dump(), "created_at": datetime.now(timezone.utc)}
    result = await db.customers.insert_one(customer_doc)
    return {"id": str(result.inserted_id), **customer_data.model_dump()}


@router.get("/customers")
async def get_customers(tenant_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {}
    if user["role"] == "super_admin":
        if tenant_id:
            query["tenant_id"] = tenant_id
    else:
        query["tenant_id"] = user.get("tenant_id")
    customers = []
    async for customer in db.customers.find(query):
        customer["id"] = str(customer.pop("_id"))
        customers.append(customer)
    return customers
