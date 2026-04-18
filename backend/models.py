from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "customer"
    tenant_id: Optional[str] = None


class TenantRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    business_name: str
    subdomain: str


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
    tenant_id: Optional[str] = None


class CourtCreate(BaseModel):
    venue_id: str
    name: str
    sport_type: str
    capacity: int = 10
    indoor: bool = True
    tenant_id: Optional[str] = None


class PricingRuleCreate(BaseModel):
    court_id: str
    rule_type: str
    price: float
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    tenant_id: Optional[str] = None


class BookingCreate(BaseModel):
    court_id: str
    customer_email: str
    customer_name: str
    customer_phone: Optional[str] = None
    date: str
    start_time: str
    end_time: str
    total_price: float


class RecurringBookingCreate(BaseModel):
    court_id: str
    customer_email: str
    customer_name: str
    customer_phone: Optional[str] = None
    start_date: str
    end_date: str
    start_time: str
    end_time: str
    days_of_week: List[int]
    total_price: float


class CustomerCreate(BaseModel):
    tenant_id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None


class SubscriptionPlan(BaseModel):
    plan_name: str
    plan_tier: str
    monthly_price: float
    features: Dict[str, Any]


class PaymentCheckoutRequest(BaseModel):
    booking_id: str
    origin_url: str


class RazorpayOrderRequest(BaseModel):
    booking_id: str
    amount: float
    currency: str = "INR"


class PayPalOrderRequest(BaseModel):
    booking_id: str
    return_url: str
    cancel_url: str


class SkrillPaymentRequest(BaseModel):
    booking_id: str
    return_url: str
    cancel_url: str
    status_url: str
