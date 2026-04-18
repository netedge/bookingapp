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
import razorpay
import io
import base64
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from typing import Optional, List, Dict, Any
import secrets
import stripe as stripe_lib

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()

# CORS - must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

# Constants
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ["JWT_SECRET"]
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET", "")
PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")
SKRILL_MERCHANT_EMAIL = os.environ.get("SKRILL_MERCHANT_EMAIL", "")
SKRILL_API_PASSWORD = os.environ.get("SKRILL_API_PASSWORD", "")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None

if PAYPAL_CLIENT_ID and PAYPAL_SECRET:
    environment = SandboxEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_SECRET) if PAYPAL_MODE == "sandbox" else LiveEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_SECRET)
    paypal_client = PayPalHttpClient(environment)
else:
    paypal_client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ EMAIL NOTIFICATION HELPERS ============

def build_booking_confirmation_html(booking: dict, venue_name: str, court_name: str) -> str:
    """Build the HTML template for booking confirmation email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .booking-details {{ background-color: #f0fdf4; border-left: 4px solid #059669; padding: 20px; margin: 20px 0; border-radius: 8px; }}
            .detail-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #1e1b4b; }}
            .value {{ color: #57534e; }}
            .footer {{ background-color: #f5f5f4; padding: 20px; text-align: center; color: #78716c; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Booking Confirmed!</h1>
            </div>
            <div class="content">
                <p>Hi {booking.get('customer_name', 'there')},</p>
                <p>Your booking has been confirmed. Here are your details:</p>
                
                <div class="booking-details">
                    <div class="detail-row"><span class="label">Venue:</span> <span class="value">{venue_name}</span></div>
                    <div class="detail-row"><span class="label">Court:</span> <span class="value">{court_name}</span></div>
                    <div class="detail-row"><span class="label">Date:</span> <span class="value">{booking.get('date')}</span></div>
                    <div class="detail-row"><span class="label">Time:</span> <span class="value">{booking.get('start_time')} - {booking.get('end_time')}</span></div>
                    <div class="detail-row"><span class="label">Total:</span> <span class="value">${booking.get('total_price', 0):.2f}</span></div>
                </div>
                
                <p>We look forward to seeing you!</p>
            </div>
            <div class="footer">
                <p>2026 Spancle Sports Venue Management</p>
            </div>
        </div>
    </body>
    </html>
    """


async def send_booking_confirmation_email(booking: dict, customer_email: str, venue_name: str, court_name: str):
    """Send booking confirmation email"""
    if not RESEND_API_KEY or RESEND_API_KEY == "re_demo_key":
        logger.info(f"Email notification skipped (demo mode): Booking confirmation to {customer_email}")
        return
    
    html_content = build_booking_confirmation_html(booking, venue_name, court_name)
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [customer_email],
            "subject": f"Booking Confirmed - {venue_name}",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Booking confirmation email sent to {customer_email}")
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {str(e)}")

def build_password_reset_html(name: str, reset_link: str) -> str:
    """Build the HTML template for password reset email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .btn {{ display: inline-block; padding: 14px 28px; background-color: #059669; color: white; text-decoration: none; border-radius: 12px; font-weight: bold; }}
            .footer {{ background-color: #f5f5f4; padding: 20px; text-align: center; color: #78716c; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Reset Your Password</h1>
            </div>
            <div class="content">
                <p>Hi {name},</p>
                <p>We received a request to reset your password. Click the button below to set a new password:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" class="btn">Reset Password</a>
                </p>
                <p style="color: #78716c; font-size: 14px;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 Spancle Sports Venue Management</p>
            </div>
        </div>
    </body>
    </html>
    """


async def send_booking_cancellation_email(booking: dict, customer_email: str, venue_name: str):
    """Send booking cancellation email"""
    if not RESEND_API_KEY or RESEND_API_KEY == "re_demo_key":
        logger.info(f"Email notification skipped (demo mode): Cancellation notice to {customer_email}")
        return
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .footer {{ background-color: #f5f5f4; padding: 20px; text-align: center; color: #78716c; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Booking Cancelled</h1>
            </div>
            <div class="content">
                <p>Hi {booking.get('customer_name', 'there')},</p>
                <p>Your booking at {venue_name} on {booking.get('date')} at {booking.get('start_time')} has been cancelled.</p>
                <p>If you have any questions, please contact the venue directly.</p>
            </div>
            <div class="footer">
                <p>© 2026 Spancle Sports Venue Management</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [customer_email],
            "subject": f"Booking Cancelled - {venue_name}",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Cancellation email sent to {customer_email}")
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {str(e)}")


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

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

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
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@spancle.com")
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

async def verify_credentials(email: str, password: str, identifier: str) -> dict:
    """Verify user credentials and handle brute force protection. Returns user dict or raises HTTPException."""
    attempt_record = await db.login_attempts.find_one({"identifier": identifier})
    if attempt_record:
        locked_until = attempt_record.get("locked_until")
        if locked_until:
            # Ensure timezone-aware comparison
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
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    await db.login_attempts.delete_one({"identifier": identifier})
    return user


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set HTTP-only auth cookies on the response."""
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


@api_router.post("/auth/login")
async def login(request: LoginRequest, response: Response, http_request: Request):
    email = request.email.lower()
    ip = http_request.client.host
    identifier = f"{ip}:{email}"
    
    user = await verify_credentials(email, request.password, identifier)
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email, user["role"])
    refresh_token = create_refresh_token(user_id)
    
    set_auth_cookies(response, access_token, refresh_token)
    
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


@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    email = request.email.lower()
    user = await db.users.find_one({"email": email})

    # Always return success to prevent email enumeration
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

    app_domain = os.environ.get("APP_DOMAIN", "spancle.com")
    frontend_url = os.environ.get("REACT_APP_FRONTEND_URL", f"https://{app_domain}")
    reset_link = f"{frontend_url}/reset-password?token={token}"

    if RESEND_API_KEY and RESEND_API_KEY != "re_demo_key":
        try:
            html = build_password_reset_html(user.get("name", "there"), reset_link)
            params = {
                "from": SENDER_EMAIL,
                "to": [email],
                "subject": "Password Reset - Spancle",
                "html": html,
            }
            await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
    else:
        logger.info(f"Password reset link (demo mode): {reset_link}")

    return {"message": "If an account with that email exists, a reset link has been sent."}


@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    record = await db.password_reset_tokens.find_one({
        "token": request.token,
        "used": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    })

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    new_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"_id": ObjectId(record["user_id"])},
        {"$set": {"password_hash": new_hash}},
    )

    await db.password_reset_tokens.update_one(
        {"token": request.token},
        {"$set": {"used": True}},
    )

    return {"message": "Password has been reset successfully"}


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
        cursor = db.tenants.find({})
        tenants = []
        async for tenant in cursor:
            tenant["id"] = str(tenant.pop("_id"))
            tenants.append(tenant)
        return tenants
    elif user["role"] == "tenant_admin" and user.get("tenant_id"):
        tenant = await db.tenants.find_one({"_id": ObjectId(user["tenant_id"])})
        if tenant:
            tenant["id"] = str(tenant.pop("_id"))
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
    
    cursor = db.venues.find(query)
    venues = []
    async for venue in cursor:
        venue["id"] = str(venue.pop("_id"))
        venues.append(venue)
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
    
    cursor = db.courts.find(query)
    courts = []
    async for court in cursor:
        court["id"] = str(court.pop("_id"))
        courts.append(court)
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
    
    cursor = db.pricing_rules.find(query)
    rules = []
    async for rule in cursor:
        rule["id"] = str(rule.pop("_id"))
        rules.append(rule)
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
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc),
        "payment_status": "pending"
    }
    
    result = await db.bookings.insert_one(booking_doc)
    booking_id = str(result.inserted_id)
    
    # Send confirmation email
    try:
        court = await db.courts.find_one({"_id": ObjectId(booking_data.court_id)})
        if court:
            venue = await db.venues.find_one({"_id": ObjectId(court.get("venue_id"))})
            if venue:
                await send_booking_confirmation_email(
                    booking_doc,
                    booking_data.customer_email,
                    venue.get("name", "Venue"),
                    court.get("name", "Court")
                )
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {str(e)}")
    
    return {"id": booking_id, **booking_data.model_dump(), "status": "confirmed"}

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
    
    cursor = db.bookings.find(query).sort("date", -1)
    bookings = []
    async for booking in cursor:
        booking["id"] = str(booking.pop("_id"))
        bookings.append(booking)
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
    cursor = db.customers.find(query)
    customers = []
    async for customer in cursor:
        customer["id"] = str(customer.pop("_id"))
        customers.append(customer)
    return customers

# ============ PAYMENT ENDPOINTS ============

class PaymentCheckoutRequest(BaseModel):
    booking_id: str
    origin_url: str

# ============ BOOKING CANCELLATION ============

@api_router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, user: dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": "cancelled"}}
    )
    
    # Send cancellation email
    try:
        court = await db.courts.find_one({"_id": ObjectId(booking.get("court_id"))})
        if court:
            venue = await db.venues.find_one({"_id": ObjectId(court.get("venue_id"))})
            if venue:
                await send_booking_cancellation_email(
                    booking,
                    booking.get("customer_email"),
                    venue.get("name", "Venue")
                )
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {str(e)}")
    
    return {"message": "Booking cancelled successfully"}

# ============ CSV EXPORT ENDPOINTS ============

@api_router.get("/export/bookings")
async def export_bookings_csv(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    query = {"tenant_id": tenant_id} if tenant_id and user["role"] != "super_admin" else {}
    
    bookings = await db.bookings.find(query).sort("date", -1).to_list(1000)
    
    csv_data = "Booking ID,Customer Name,Customer Email,Date,Start Time,End Time,Court ID,Total Price,Status,Payment Status\\n"
    for booking in bookings:
        csv_data += f"\"{str(booking['_id'])}\",\"{booking.get('customer_name', '')}\",\"{booking.get('customer_email', '')}\",\"{booking.get('date', '')}\",\"{booking.get('start_time', '')}\",\"{booking.get('end_time', '')}\",\"{booking.get('court_id', '')}\",{booking.get('total_price', 0)},\"{booking.get('status', '')}\",\"{booking.get('payment_status', '')}\"\\n"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=bookings_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@api_router.get("/export/analytics")
async def export_analytics_csv(days: int = 30, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    match_stage = {"payment_status": "paid", "created_at": {"$gte": start_date, "$lte": end_date}}
    if user["role"] != "super_admin" and tenant_id:
        match_stage["tenant_id"] = tenant_id
    
    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "revenue": {"$sum": "$total_price"},
                "bookings": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = await db.bookings.aggregate(pipeline).to_list(1000)
    
    csv_data = "Date,Revenue,Bookings\\n"
    for item in result:
        csv_data += f"\"{item['_id']}\",{item['revenue']},{item['bookings']}\\n"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# ============ RECURRING BOOKINGS ============

class RecurringBookingCreate(BaseModel):
    court_id: str
    customer_email: str
    customer_name: str
    customer_phone: Optional[str] = None
    start_date: str
    end_date: str
    start_time: str
    end_time: str
    days_of_week: List[int]  # 0=Monday, 6=Sunday
    total_price: float

def generate_recurrence_dates(start_date_str: str, end_date_str: str, days_of_week: list) -> list:
    """Generate all dates matching the recurrence pattern."""
    from datetime import datetime as dt
    start_date = dt.strptime(start_date_str, "%Y-%m-%d")
    end_date = dt.strptime(end_date_str, "%Y-%m-%d")
    dates = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in days_of_week:
            dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    return dates


def build_recurring_booking_doc(booking_data, date_str: str) -> dict:
    """Build a single booking document for a recurring series."""
    return {
        "court_id": booking_data.court_id,
        "customer_email": booking_data.customer_email,
        "customer_name": booking_data.customer_name,
        "customer_phone": booking_data.customer_phone,
        "date": date_str,
        "start_time": booking_data.start_time,
        "end_time": booking_data.end_time,
        "total_price": booking_data.total_price,
        "status": "confirmed",
        "payment_status": "pending",
        "recurring": True,
        "created_at": datetime.now(timezone.utc)
    }


@api_router.post("/bookings/recurring")
async def create_recurring_booking(booking_data: RecurringBookingCreate, user: dict = Depends(get_current_user)):
    dates = generate_recurrence_dates(booking_data.start_date, booking_data.end_date, booking_data.days_of_week)
    
    created_bookings = []
    conflicts = []
    
    for date_str in dates:
        existing = await db.bookings.find_one({
            "court_id": booking_data.court_id,
            "date": date_str,
            "status": {"$in": ["pending", "confirmed"]},
            "$or": [
                {
                    "start_time": {"$lt": booking_data.end_time},
                    "end_time": {"$gt": booking_data.start_time}
                }
            ]
        })
        
        if not existing:
            booking_doc = build_recurring_booking_doc(booking_data, date_str)
            result = await db.bookings.insert_one(booking_doc)
            created_bookings.append({"date": date_str, "id": str(result.inserted_id)})
        else:
            conflicts.append(date_str)
    
    return {
        "created_count": len(created_bookings),
        "conflict_count": len(conflicts),
        "created_bookings": created_bookings,
        "conflicts": conflicts
    }

# ============ SUBSCRIPTION TIERS ============

class SubscriptionPlan(BaseModel):
    plan_name: str
    plan_tier: str  # "basic", "pro", "enterprise"
    monthly_price: float
    features: Dict[str, Any]

@api_router.get("/subscriptions/plans")
async def get_subscription_plans():
    plans = [
        {
            "plan_tier": "basic",
            "plan_name": "Basic",
            "monthly_price": 49.00,
            "features": {
                "max_venues": 1,
                "max_courts": 5,
                "max_bookings_per_month": 100,
                "analytics": False,
                "custom_domain": False,
                "email_notifications": True,
                "priority_support": False
            }
        },
        {
            "plan_tier": "pro",
            "plan_name": "Professional",
            "monthly_price": 149.00,
            "features": {
                "max_venues": 5,
                "max_courts": 25,
                "max_bookings_per_month": 500,
                "analytics": True,
                "custom_domain": True,
                "email_notifications": True,
                "priority_support": True
            }
        },
        {
            "plan_tier": "enterprise",
            "plan_name": "Enterprise",
            "monthly_price": 499.00,
            "features": {
                "max_venues": "unlimited",
                "max_courts": "unlimited",
                "max_bookings_per_month": "unlimited",
                "analytics": True,
                "custom_domain": True,
                "email_notifications": True,
                "priority_support": True,
                "white_label": True,
                "api_access": True
            }
        }
    ]
    return plans

@api_router.put("/tenants/{tenant_id}/subscription")
async def update_tenant_subscription(
    tenant_id: str,
    plan_tier: str,
    user: dict = Depends(get_current_user)
):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can update subscriptions")
    
    await db.tenants.update_one(
        {"_id": ObjectId(tenant_id)},
        {"$set": {
            "subscription_tier": plan_tier,
            "subscription_updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"message": "Subscription updated successfully"}

@api_router.post("/payments/checkout")
async def create_checkout_session(
    request: PaymentCheckoutRequest,
    user: dict = Depends(get_current_user)
):
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    stripe_lib.api_key = os.environ.get("STRIPE_API_KEY")
    
    success_url = f"{request.origin_url}/booking-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/booking-cancel"
    
    session = stripe_lib.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": int(booking["total_price"] * 100),
                "product_data": {"name": f"Booking {request.booking_id}"},
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"booking_id": request.booking_id},
    )
    
    # Store payment transaction
    await db.payment_transactions.insert_one({
        "booking_id": request.booking_id,
        "session_id": session.id,
        "amount": booking["total_price"],
        "currency": "usd",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {"url": session.url, "session_id": session.id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    stripe_lib.api_key = os.environ.get("STRIPE_API_KEY")
    
    session = stripe_lib.checkout.Session.retrieve(session_id)
    payment_status = "paid" if session.payment_status == "paid" else session.payment_status
    
    # Update payment transaction
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": payment_status}}
    )
    
    if payment_status == "paid":
        # Update booking status
        tx = await db.payment_transactions.find_one({"session_id": session_id})
        if tx:
            await db.bookings.update_one(
                {"_id": ObjectId(tx["booking_id"])},
                {"$set": {"status": "confirmed", "payment_status": "paid"}}
            )
    
    return {"session_id": session_id, "payment_status": payment_status, "amount_total": session.amount_total}


# ============ RAZORPAY PAYMENT ENDPOINTS ============

class RazorpayOrderRequest(BaseModel):
    booking_id: str
    amount: float
    currency: str = "INR"

@api_router.post("/payments/razorpay/create-order")
async def create_razorpay_order(request: RazorpayOrderRequest, user: dict = Depends(get_current_user)):
    if not razorpay_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Amount in paise (multiply by 100)
    amount_paise = int(request.amount * 100)
    
    try:
        order_data = {
            "amount": amount_paise,
            "currency": request.currency,
            "payment_capture": 1,
            "notes": {
                "booking_id": request.booking_id
            }
        }
        
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        # Store payment transaction
        await db.payment_transactions.insert_one({
            "booking_id": request.booking_id,
            "razorpay_order_id": razorpay_order["id"],
            "amount": request.amount,
            "currency": request.currency,
            "payment_status": "created",
            "payment_method": "razorpay",
            "created_at": datetime.now(timezone.utc)
        })
        
        return {
            "order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "key_id": RAZORPAY_KEY_ID
        }
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment order creation failed: {str(e)}")

@api_router.post("/payments/razorpay/verify")
async def verify_razorpay_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
):
    if not razorpay_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    try:
        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update payment transaction
        await db.payment_transactions.update_one(
            {"razorpay_order_id": razorpay_order_id},
            {
                "$set": {
                    "razorpay_payment_id": razorpay_payment_id,
                    "payment_status": "paid",
                    "verified_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Update booking status
        tx = await db.payment_transactions.find_one({"razorpay_order_id": razorpay_order_id})
        if tx:
            await db.bookings.update_one(
                {"_id": ObjectId(tx["booking_id"])},
                {"$set": {"status": "confirmed", "payment_status": "paid"}}
            )
        
        return {"status": "success", "message": "Payment verified successfully"}
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment verification failed")

# ============ PAYPAL PAYMENT ENDPOINTS ============

class PayPalOrderRequest(BaseModel):
    booking_id: str
    return_url: str
    cancel_url: str

def build_paypal_order_body(booking_id: str, amount: float, return_url: str, cancel_url: str) -> dict:
    """Build the PayPal order request body."""
    return {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": booking_id,
            "amount": {
                "currency_code": "USD",
                "value": f"{amount:.2f}"
            }
        }],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }


def extract_paypal_approval_url(links) -> str:
    """Extract the approval URL from PayPal response links."""
    for link in links:
        if link.rel == "approve":
            return link.href
    return None


@api_router.post("/payments/paypal/create-order")
async def create_paypal_order(request: PayPalOrderRequest, user: dict = Depends(get_current_user)):
    if not paypal_client:
        raise HTTPException(status_code=400, detail="PayPal not configured")
    
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    try:
        order_request = OrdersCreateRequest()
        order_request.prefer('return=representation')
        order_request.request_body(
            build_paypal_order_body(request.booking_id, booking['total_price'], request.return_url, request.cancel_url)
        )
        
        response = paypal_client.execute(order_request)
        
        await db.payment_transactions.insert_one({
            "booking_id": request.booking_id,
            "paypal_order_id": response.result.id,
            "amount": booking["total_price"],
            "currency": "USD",
            "payment_status": "created",
            "payment_method": "paypal",
            "created_at": datetime.now(timezone.utc)
        })
        
        return {
            "order_id": response.result.id,
            "status": response.result.status,
            "approval_url": extract_paypal_approval_url(response.result.links)
        }
    except Exception as e:
        logger.error(f"PayPal order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment order creation failed: {str(e)}")

@api_router.post("/payments/paypal/capture/{order_id}")
async def capture_paypal_order(order_id: str):
    if not paypal_client:
        raise HTTPException(status_code=400, detail="PayPal not configured")
    
    try:
        capture_request = OrdersCaptureRequest(order_id)
        response = paypal_client.execute(capture_request)
        
        # Update payment transaction
        await db.payment_transactions.update_one(
            {"paypal_order_id": order_id},
            {
                "$set": {
                    "payment_status": "paid",
                    "captured_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Update booking status
        tx = await db.payment_transactions.find_one({"paypal_order_id": order_id})
        if tx:
            await db.bookings.update_one(
                {"_id": ObjectId(tx["booking_id"])},
                {"$set": {"status": "confirmed", "payment_status": "paid"}}
            )
        
        return {
            "status": "success",
            "order_id": order_id,
            "capture_id": response.result.purchase_units[0].payments.captures[0].id
        }
    except Exception as e:
        logger.error(f"PayPal capture failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment capture failed")

# ============ SKRILL PAYMENT ENDPOINTS ============

class SkrillPaymentRequest(BaseModel):
    booking_id: str
    return_url: str
    cancel_url: str
    status_url: str

def build_skrill_payload(booking: dict, request) -> dict:
    """Build the Skrill payment request payload."""
    return {
        "pay_to_email": SKRILL_MERCHANT_EMAIL,
        "amount": f"{booking['total_price']:.2f}",
        "currency": "EUR",
        "return_url": request.return_url,
        "cancel_url": request.cancel_url,
        "status_url": request.status_url,
        "transaction_id": str(booking["_id"]),
        "detail1_description": f"Booking: {booking.get('customer_name', '')}",
        "detail1_text": f"Date: {booking.get('date', '')} {booking.get('start_time', '')}"
    }


@api_router.post("/payments/skrill/prepare")
async def prepare_skrill_payment(request: SkrillPaymentRequest):
    if not SKRILL_MERCHANT_EMAIL or not SKRILL_API_PASSWORD:
        raise HTTPException(status_code=400, detail="Skrill not configured")
    
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    try:
        payload = build_skrill_payload(booking, request)
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post("https://pay.skrill.com", data=payload, timeout=30)
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to create Skrill session")
            
            session_id = response.text
            
            await db.payment_transactions.insert_one({
                "booking_id": request.booking_id,
                "skrill_session_id": session_id,
                "amount": booking["total_price"],
                "currency": "EUR",
                "payment_status": "created",
                "payment_method": "skrill",
                "created_at": datetime.now(timezone.utc)
            })
            
            return {
                "session_id": session_id,
                "payment_url": f"https://pay.skrill.com/?sid={session_id}"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skrill payment preparation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment preparation failed: {str(e)}")

@api_router.post("/payments/skrill/status")
async def skrill_payment_status(request: Request):
    """Webhook endpoint for Skrill payment status updates"""
    try:
        form_data = await request.form()
        
        transaction_id = form_data.get("transaction_id")
        status = form_data.get("status")
        mb_transaction_id = form_data.get("mb_transaction_id")
        
        # Update payment transaction
        await db.payment_transactions.update_one(
            {"booking_id": transaction_id},
            {
                "$set": {
                    "payment_status": "paid" if status == "2" else "failed",
                    "skrill_transaction_id": mb_transaction_id,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Update booking if payment successful
        if status == "2":  # Processed
            booking = await db.bookings.find_one({"_id": ObjectId(transaction_id)})
            if booking:
                await db.bookings.update_one(
                    {"_id": ObjectId(transaction_id)},
                    {"$set": {"status": "confirmed", "payment_status": "paid"}}
                )
        
        return {"status": "processed"}
    except Exception as e:
        logger.error(f"Skrill webhook processing failed: {str(e)}")
        return {"status": "error"}

@api_router.get("/payments/razorpay/status/{order_id}")
async def get_razorpay_payment_status(order_id: str):
    if not razorpay_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    try:
        order = razorpay_client.order.fetch(order_id)
        payments = razorpay_client.order.payments(order_id)
        
        tx = await db.payment_transactions.find_one({"razorpay_order_id": order_id})
        
        return {
            "order_id": order_id,
            "status": order["status"],
            "amount_paid": order.get("amount_paid", 0) / 100,
            "payment_status": tx.get("payment_status") if tx else "unknown",
            "payments": payments.get("items", [])
        }
    except Exception as e:
        logger.error(f"Failed to fetch payment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment status")



@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_lib.api_key = os.environ.get("STRIPE_API_KEY")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    
    try:
        if webhook_secret:
            event = stripe_lib.Webhook.construct_event(body, signature, webhook_secret)
        else:
            import json
            event = json.loads(body)
        logger.info(f"Webhook received: {event.get('type', 'unknown')}")
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
    app_domain = os.environ.get("APP_DOMAIN", "spancle.com")
    booking_url = f"https://{tenant['subdomain']}.{app_domain}/book/{venue_id}"
    
    qr_code_data = generate_qr_code(booking_url)
    
    return {
        "qr_code": qr_code_data,
        "booking_url": booking_url
    }

# ============ PUBLIC ENDPOINTS (NO AUTH) ============

@api_router.get("/public/tenant/{subdomain}")
async def get_tenant_by_subdomain(subdomain: str):
    tenant = await db.tenants.find_one({"subdomain": subdomain})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant_id = str(tenant["_id"])
    
    # Get venues for this tenant
    venues_cursor = db.venues.find({"tenant_id": tenant_id})
    venues = []
    async for v in venues_cursor:
        venues.append({
            "id": str(v["_id"]),
            "name": v.get("name", ""),
            "description": v.get("description", ""),
            "address": v.get("address", ""),
            "image_url": v.get("image_url", ""),
        })
    
    return {
        "tenant_id": tenant_id,
        "business_name": tenant.get("business_name", ""),
        "subdomain": tenant.get("subdomain", ""),
        "subscription_tier": tenant.get("subscription_tier", "free"),
        "venues": venues
    }

@api_router.get("/public/venue/{venue_id}")
async def get_public_venue(venue_id: str):
    venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Get courts for this venue
    courts_cursor = db.courts.find({"venue_id": venue_id})
    courts = []
    async for c in courts_cursor:
        courts.append({
            "id": str(c["_id"]),
            "name": c.get("name", ""),
            "sport_type": c.get("sport_type", ""),
            "venue_id": c.get("venue_id", ""),
        })
    
    return {
        "id": str(venue["_id"]),
        "name": venue.get("name", ""),
        "description": venue.get("description", ""),
        "address": venue.get("address", ""),
        "image_url": venue.get("image_url", ""),
        "tenant_id": venue.get("tenant_id", ""),
        "courts": courts
    }

@api_router.get("/public/courts/{venue_id}")
async def get_public_courts(venue_id: str):
    courts_cursor = db.courts.find({"venue_id": venue_id})
    courts = []
    async for c in courts_cursor:
        courts.append({
            "id": str(c["_id"]),
            "name": c.get("name", ""),
            "sport_type": c.get("sport_type", ""),
            "venue_id": c.get("venue_id", ""),
        })
    return courts

@api_router.get("/public/bookings")
async def get_public_bookings(court_id: str = Query(...), date: str = Query(...)):
    bookings = await db.bookings.find(
        {"court_id": court_id, "date": date, "status": {"$ne": "cancelled"}},
        {"_id": 0}
    ).to_list(100)
    return bookings

@api_router.post("/public/bookings")
async def create_public_booking(booking: BookingCreate):
    booking_doc = {
        "court_id": booking.court_id,
        "customer_name": booking.customer_name,
        "customer_email": booking.customer_email,
        "customer_phone": booking.customer_phone,
        "date": booking.date,
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "total_price": booking.total_price,
        "status": "pending",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.bookings.insert_one(booking_doc)
    booking_id = str(result.inserted_id)
    
    return {"id": booking_id, "status": "pending", "message": "Booking created successfully"}

# Include router
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
