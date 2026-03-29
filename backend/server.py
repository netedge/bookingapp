from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import os
import logging
import bcrypt
import jwt
import asyncio
import resend
import qrcode
import io
import base64
from typing import Optional, List, Dict, Any
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Constants
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ["JWT_SECRET"]
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ HELPER FUNCTIONS ============

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def generate_qr_code(data: str) -> str:
    """Generate QR code and return base64 encoded image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# ============ PYDANTIC MODELS ============

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "customer"
    tenant_id: Optional[str] = None

class TenantCreate(BaseModel):
    business_name: str
    admin_email: EmailStr
    admin_password: str
    admin_name: str
    subdomain: str
    timezone: str = "UTC"
    currency: str = "USD"

class TenantUpdate(BaseModel):
    business_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None

class VenueCreate(BaseModel):
    name: str
    description: str
    address: str
    image_url: Optional[str] = None
    tenant_id: Optional[str] = None  # Allow super_admin to specify tenant

class CourtCreate(BaseModel):
    venue_id: str
    name: str
    sport_type: str
    capacity: int = 10
    indoor: bool = True
    tenant_id: Optional[str] = None  # Allow super_admin to specify tenant

class PricingRuleCreate(BaseModel):
    court_id: str
    rule_type: str  # "hourly", "peak", "weekend"
    price: float
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    tenant_id: Optional[str] = None  # Allow super_admin to specify tenant

class BookingCreate(BaseModel):
    court_id: str
    customer_email: str
    customer_name: str
    customer_phone: Optional[str] = None
    date: str
    start_time: str
    end_time: str
    total_price: float

class CustomerCreate(BaseModel):
    tenant_id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None

# ============ STARTUP & SEEDING ============

@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.tenants.create_index("subdomain", unique=True)
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.login_attempts.create_index("identifier")
    
    # Seed super admin
    await seed_admin()

async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@kelika.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "Super Admin",
            "role": "super_admin",
            "tenant_id": None,
            "created_at": datetime.now(timezone.utc)
        })
        logger.info(f"Super admin created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        logger.info("Super admin password updated")
    
    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write("## Super Admin\n")
        f.write(f"- Email: {admin_email}\n")
        f.write(f"- Password: {admin_password}\n")
        f.write(f"- Role: super_admin\n\n")
        f.write("## Endpoints\n")
        f.write("- Login: POST /api/auth/login\n")
        f.write("- Register: POST /api/auth/register\n")
        f.write("- Me: GET /api/auth/me\n")

# ============ AUTH ENDPOINTS ============

@api_router.post("/auth/register")
async def register(request: RegisterRequest, response: Response):
    email = request.email.lower()
    
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    password_hash = hash_password(request.password)
    
    user_data = {
        "email": email,
        "password_hash": password_hash,
        "name": request.name,
        "role": request.role,
        "tenant_id": request.tenant_id,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email, request.role)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=900,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800,
        path="/"
    )
    
    return {
        "id": user_id,
        "email": email,
        "name": request.name,
        "role": request.role,
        "tenant_id": request.tenant_id
    }

@api_router.post("/auth/login")
async def login(request: LoginRequest, response: Response, http_request: Request):
    email = request.email.lower()
    ip = http_request.client.host
    identifier = f"{ip}:{email}"
    
    # Check brute force
    attempt_record = await db.login_attempts.find_one({"identifier": identifier})
    if attempt_record:
        if attempt_record.get("locked_until") and attempt_record["locked_until"] > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(request.password, user["password_hash"]):
        # Increment failed attempts
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {
                "$inc": {"attempts": 1},
                "$set": {
                    "last_attempt": datetime.now(timezone.utc),
                    "locked_until": datetime.now(timezone.utc) + timedelta(minutes=15)
                }
            },
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Clear failed attempts
    await db.login_attempts.delete_one({"identifier": identifier})
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email, user["role"])
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=900,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800,
        path="/"
    )
    
    return {
        "id": user_id,
        "email": email,
        "name": user["name"],
        "role": user["role"],
        "tenant_id": user.get("tenant_id")
    }

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

# ============ TENANT ENDPOINTS ============

@api_router.post("/tenants")
async def create_tenant(tenant_data: TenantCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can create tenants")
    
    # Check subdomain availability
    existing = await db.tenants.find_one({"subdomain": tenant_data.subdomain})
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")
    
    # Create tenant
    tenant_doc = {
        "business_name": tenant_data.business_name,
        "subdomain": tenant_data.subdomain,
        "logo_url": None,
        "primary_color": "#059669",  # Emerald
        "timezone": tenant_data.timezone,
        "currency": tenant_data.currency,
        "created_at": datetime.now(timezone.utc),
        "status": "active"
    }
    
    tenant_result = await db.tenants.insert_one(tenant_doc)
    tenant_id = str(tenant_result.inserted_id)
    
    # Create tenant admin
    admin_hash = hash_password(tenant_data.admin_password)
    admin_doc = {
        "email": tenant_data.admin_email.lower(),
        "password_hash": admin_hash,
        "name": tenant_data.admin_name,
        "role": "tenant_admin",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(admin_doc)
    
    return {
        "id": tenant_id,
        "business_name": tenant_data.business_name,
        "subdomain": tenant_data.subdomain,
        "admin_email": tenant_data.admin_email
    }

@api_router.get("/tenants")
async def get_tenants(user: dict = Depends(get_current_user)):
    if user["role"] == "super_admin":
        tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
        for tenant in tenants:
            tenant["id"] = tenant.pop("_id", None)
        return tenants
    elif user["role"] == "tenant_admin":
        tenant = await db.tenants.find_one({"_id": ObjectId(user["tenant_id"])}, {"_id": 0})
        if tenant:
            tenant["id"] = user["tenant_id"]
            return [tenant]
    return []

@api_router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"_id": ObjectId(tenant_id)}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant["id"] = tenant_id
    return tenant

@api_router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, update_data: TenantUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if user["role"] == "tenant_admin" and user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Can only update own tenant")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if update_dict:
        await db.tenants.update_one({"_id": ObjectId(tenant_id)}, {"$set": update_dict})
    
    return {"message": "Tenant updated successfully"}

# ============ VENUE ENDPOINTS ============

@api_router.post("/venues")
async def create_venue(venue_data: VenueCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Determine tenant_id
    if user["role"] == "super_admin":
        if not venue_data.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required for super_admin")
        tenant_id = venue_data.tenant_id
    else:
        tenant_id = user["tenant_id"]
    
    venue_doc = {
        "tenant_id": tenant_id,
        "name": venue_data.name,
        "description": venue_data.description,
        "address": venue_data.address,
        "image_url": venue_data.image_url or "https://images.unsplash.com/photo-1765124540460-b884e248ac2b",
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.venues.insert_one(venue_doc)
    venue_id = str(result.inserted_id)
    
    return {"id": venue_id, **venue_data.model_dump()}

@api_router.get("/venues")
async def get_venues(tenant_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {}
    
    if user["role"] == "super_admin":
        if tenant_id:
            query["tenant_id"] = tenant_id
    else:
        query["tenant_id"] = user["tenant_id"]
    
    venues = await db.venues.find(query, {"_id": 0}).to_list(100)
    return venues

# ============ COURT ENDPOINTS ============

@api_router.post("/courts")
async def create_court(court_data: CourtCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Determine tenant_id
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
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.courts.insert_one(court_doc)
    court_id = str(result.inserted_id)
    
    return {"id": court_id, **court_data.model_dump()}

@api_router.get("/courts")
async def get_courts(venue_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {"tenant_id": user.get("tenant_id")}
    if venue_id:
        query["venue_id"] = venue_id
    
    courts = await db.courts.find(query, {"_id": 0}).to_list(100)
    return courts

# ============ PRICING ENDPOINTS ============

@api_router.post("/pricing")
async def create_pricing_rule(pricing_data: PricingRuleCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Determine tenant_id
    if user["role"] == "super_admin":
        if not pricing_data.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required for super_admin")
        tenant_id = pricing_data.tenant_id
    else:
        tenant_id = user["tenant_id"]
    
    pricing_doc = {
        "tenant_id": tenant_id,
        "court_id": pricing_data.court_id,
        "rule_type": pricing_data.rule_type,
        "price": pricing_data.price,
        "start_time": pricing_data.start_time,
        "end_time": pricing_data.end_time,
        "days_of_week": pricing_data.days_of_week,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.pricing_rules.insert_one(pricing_doc)
    return {"id": str(result.inserted_id), **pricing_data.model_dump()}

@api_router.get("/pricing")
async def get_pricing_rules(court_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    query = {"tenant_id": user.get("tenant_id")}
    if court_id:
        query["court_id"] = court_id
    
    rules = await db.pricing_rules.find(query, {"_id": 0}).to_list(100)
    return rules

# ============ BOOKING ENDPOINTS ============

@api_router.post("/bookings")
async def create_booking(booking_data: BookingCreate):
    # Check for conflicts
    existing = await db.bookings.find_one({
        "court_id": booking_data.court_id,
        "date": booking_data.date,
        "status": {"$in": ["pending", "confirmed"]},
        "$or": [
            {
                "start_time": {"$lt": booking_data.end_time},
                "end_time": {"$gt": booking_data.start_time}
            }
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Slot already booked")
    
    booking_doc = {
        **booking_data.model_dump(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "payment_status": "pending"
    }
    
    result = await db.bookings.insert_one(booking_doc)
    booking_id = str(result.inserted_id)
    
    return {"id": booking_id, **booking_data.model_dump(), "status": "pending"}

@api_router.get("/bookings")
async def get_bookings(
    court_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    query = {}
    if court_id:
        query["court_id"] = court_id
    if date:
        query["date"] = date
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("date", -1).to_list(100)
    return bookings

# ============ CUSTOMER ENDPOINTS ============

@api_router.post("/customers")
async def create_customer(customer_data: CustomerCreate, user: dict = Depends(get_current_user)):
    customer_doc = {
        **customer_data.model_dump(),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.customers.insert_one(customer_doc)
    return {"id": str(result.inserted_id), **customer_data.model_dump()}

@api_router.get("/customers")
async def get_customers(user: dict = Depends(get_current_user)):
    query = {"tenant_id": user.get("tenant_id")}
    customers = await db.customers.find(query, {"_id": 0}).to_list(100)
    return customers

# ============ PAYMENT ENDPOINTS ============

class PaymentCheckoutRequest(BaseModel):
    booking_id: str
    origin_url: str

@api_router.post("/payments/checkout")
async def create_checkout_session(
    request: PaymentCheckoutRequest,
    user: dict = Depends(get_current_user)
):
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    stripe_key = os.environ.get("STRIPE_API_KEY")
    webhook_url = f"{request.origin_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    
    success_url = f"{request.origin_url}/booking-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/booking-cancel"
    
    checkout_request = CheckoutSessionRequest(
        amount=booking["total_price"],
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"booking_id": request.booking_id}
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Store payment transaction
    await db.payment_transactions.insert_one({
        "booking_id": request.booking_id,
        "session_id": session.session_id,
        "amount": booking["total_price"],
        "currency": "usd",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    stripe_key = os.environ.get("STRIPE_API_KEY")
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url="")
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update payment transaction
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": status.payment_status}}
    )
    
    if status.payment_status == "paid":
        # Update booking status
        tx = await db.payment_transactions.find_one({"session_id": session_id})
        if tx:
            await db.bookings.update_one(
                {"_id": ObjectId(tx["booking_id"])},
                {"$set": {"status": "confirmed", "payment_status": "paid"}}
            )
    
    return status.model_dump()

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_key = os.environ.get("STRIPE_API_KEY")
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url="")
    
    try:
        event = await stripe_checkout.handle_webhook(body, signature)
        logger.info(f"Webhook received: {event.event_type}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============ ANALYTICS ENDPOINTS ============

@api_router.get("/analytics/dashboard")
async def get_analytics(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    
    # For super_admin, show aggregated stats; for others, show tenant-specific
    if user["role"] == "super_admin":
        total_bookings = await db.bookings.count_documents({})
        total_venues = await db.venues.count_documents({})
        total_customers = await db.customers.count_documents({})
        revenue_pipeline = [
            {"$match": {"payment_status": "paid"}},
            {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}
        ]
    else:
        total_bookings = await db.bookings.count_documents({"tenant_id": tenant_id}) if tenant_id else 0
        total_venues = await db.venues.count_documents({"tenant_id": tenant_id}) if tenant_id else 0
        total_customers = await db.customers.count_documents({"tenant_id": tenant_id}) if tenant_id else 0
        revenue_pipeline = [
            {"$match": {"payment_status": "paid", "tenant_id": tenant_id}},
            {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}
        ] if tenant_id else []
    
    if revenue_pipeline:
        revenue_result = await db.bookings.aggregate(revenue_pipeline).to_list(1)
        total_revenue = revenue_result[0]["total"] if revenue_result else 0
    else:
        total_revenue = 0
    
    return {
        "total_bookings": total_bookings,
        "total_venues": total_venues,
        "total_customers": total_customers,
        "total_revenue": total_revenue
    }

# ============ BULK IMPORT ENDPOINTS ============

@api_router.post("/bulk-import/venues")
async def bulk_import_venues(venues_data: List[VenueCreate], user: dict = Depends(get_current_user)):
    if user["role"] not in ["super_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    imported = []
    errors = []
    
    for idx, venue_data in enumerate(venues_data):
        try:
            # Determine tenant_id
            if user["role"] == "super_admin":
                if not venue_data.tenant_id:
                    errors.append({"index": idx, "error": "tenant_id required for super_admin"})
                    continue
                tenant_id = venue_data.tenant_id
            else:
                tenant_id = user["tenant_id"]
            
            venue_doc = {
                "tenant_id": tenant_id,
                "name": venue_data.name,
                "description": venue_data.description,
                "address": venue_data.address,
                "image_url": venue_data.image_url or "https://images.unsplash.com/photo-1765124540460-b884e248ac2b",
                "created_at": datetime.now(timezone.utc)
            }
            
            result = await db.venues.insert_one(venue_doc)
            imported.append({"index": idx, "id": str(result.inserted_id), "name": venue_data.name})
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})
    
    return {
        "imported_count": len(imported),
        "error_count": len(errors),
        "imported": imported,
        "errors": errors
    }

# ============ ANALYTICS CHART DATA ENDPOINTS ============

@api_router.get("/analytics/revenue-trend")
async def get_revenue_trend(days: int = 30, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Build aggregation pipeline
    match_stage = {"payment_status": "paid", "created_at": {"$gte": start_date, "$lte": end_date}}
    if user["role"] != "super_admin" and tenant_id:
        match_stage["tenant_id"] = tenant_id
    
    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "revenue": {"$sum": "$total_price"},
                "bookings": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = await db.bookings.aggregate(pipeline).to_list(100)
    
    return {
        "dates": [item["_id"] for item in result],
        "revenue": [item["revenue"] for item in result],
        "bookings": [item["bookings"] for item in result]
    }

@api_router.get("/analytics/court-occupancy")
async def get_court_occupancy(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    
    # Get all courts (keep _id for matching)
    court_query = {"tenant_id": tenant_id} if tenant_id and user["role"] != "super_admin" else {}
    courts = await db.courts.find(court_query).to_list(100)
    
    if not courts:
        return []
    
    # Get booking counts for all courts in one query (prevents N+1)
    court_ids = [str(court["_id"]) for court in courts]
    
    booking_pipeline = [
        {"$match": {"court_id": {"$in": court_ids}, "status": {"$in": ["confirmed", "completed"]}}},
        {"$group": {"_id": "$court_id", "count": {"$sum": 1}}}
    ]
    booking_counts = await db.bookings.aggregate(booking_pipeline).to_list(100)
    booking_map = {item["_id"]: item["count"] for item in booking_counts}
    
    occupancy_data = []
    for court in courts:
        court_id = str(court["_id"])
        booking_count = booking_map.get(court_id, 0)
        
        occupancy_data.append({
            "court_name": court.get("name"),
            "sport_type": court.get("sport_type"),
            "bookings": booking_count,
            "occupancy_rate": min(booking_count / 30 * 100, 100)
        })
    
    return sorted(occupancy_data, key=lambda x: x["occupancy_rate"], reverse=True)

# ============ QR CODE ENDPOINTS ============

@api_router.get("/qr-code/{venue_id}")
async def get_venue_qr_code(venue_id: str, user: dict = Depends(get_current_user)):
    venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    tenant = await db.tenants.find_one({"_id": ObjectId(venue["tenant_id"])})
    app_domain = os.environ.get("APP_DOMAIN", "emergent.host")
    booking_url = f"https://{tenant['subdomain']}.{app_domain}/book/{venue_id}"
    
    qr_code_data = generate_qr_code(booking_url)
    
    return {
        "qr_code": qr_code_data,
        "booking_url": booking_url
    }

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
