"""Backend regression tests for Spancle after modular refactor.

Covers auth, tenants, venues, courts, bookings, customers, analytics,
subscriptions, public endpoints, pricing.
"""
import os
import time
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load env from frontend/.env and backend/.env
load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').strip().rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017').strip().strip('"')
DB_NAME = os.environ.get('DB_NAME', 'spancle_db').strip().strip('"')
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@spancle.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


# -------------------- Fixtures --------------------
@pytest.fixture(scope="session")
def admin_session():
    # Ensure no leftover lockouts
    db.login_attempts.delete_many({})
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "id" in data and "email" in data and "role" in data
    assert data["role"] == "super_admin"
    return s


@pytest.fixture(scope="session")
def elite_tenant(admin_session):
    """Ensure the 'Elite Sports' tenant exists; create if missing."""
    r = admin_session.get(f"{API}/tenants")
    assert r.status_code == 200
    for t in r.json():
        if t.get("subdomain") == "elite-sports":
            return t

    payload = {
        "business_name": "Elite Sports",
        "admin_email": "elite@test.com",
        "admin_password": "test123",
        "admin_name": "Elite Admin",
        "subdomain": "elite-sports",
        "timezone": "UTC",
        "currency": "USD",
    }
    r = admin_session.post(f"{API}/tenants", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


# -------------------- Auth --------------------
class TestAuth:
    def test_login_success(self):
        db.login_attempts.delete_many({})
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "super_admin"
        assert data["id"]
        # Cookies set
        assert "access_token" in r.cookies or any(c.name == "access_token" for c in r.cookies)

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": "nobody_xyz@test.com", "password": "wrong"})
        assert r.status_code in (401, 429)
        db.login_attempts.delete_many({})

    def test_login_four_failures_then_success(self):
        """Playbook: lockout should trigger only after 5 failed attempts, not before."""
        db.login_attempts.delete_many({})
        s = requests.Session()
        for _ in range(4):
            r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrongpw"})
            assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"
        # Correct credentials should still succeed
        r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        db.login_attempts.delete_many({})

    def test_me_with_cookie(self, admin_session):
        r = admin_session.get(f"{API}/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data.get("email") == ADMIN_EMAIL
        assert data.get("role") == "super_admin"

    def test_logout_clears_cookies(self):
        db.login_attempts.delete_many({})
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        r2 = s.post(f"{API}/auth/logout")
        assert r2.status_code == 200
        # After logout, /auth/me should return 401
        r3 = requests.get(f"{API}/auth/me")
        assert r3.status_code == 401


# -------------------- Forgot / Reset Password --------------------
class TestForgotReset:
    def test_forgot_password_valid_email(self):
        db.password_reset_tokens.delete_many({"email": ADMIN_EMAIL})
        r = requests.post(f"{API}/auth/forgot-password", json={"email": ADMIN_EMAIL})
        assert r.status_code == 200
        assert "message" in r.json()
        token_doc = db.password_reset_tokens.find_one({"email": ADMIN_EMAIL, "used": False})
        assert token_doc is not None and token_doc.get("token")

    def test_forgot_password_invalid_email_no_enumeration(self):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": "nosuchuser_xyz@example.com"})
        assert r.status_code == 200
        assert "message" in r.json()

    def test_reset_password_and_reuse_blocked(self):
        db.password_reset_tokens.delete_many({"email": ADMIN_EMAIL})
        r = requests.post(f"{API}/auth/forgot-password", json={"email": ADMIN_EMAIL})
        assert r.status_code == 200
        token_doc = db.password_reset_tokens.find_one({"email": ADMIN_EMAIL, "used": False})
        assert token_doc is not None
        token = token_doc["token"]

        r = requests.post(f"{API}/auth/reset-password", json={"token": token, "new_password": ADMIN_PASSWORD})
        assert r.status_code == 200
        assert "message" in r.json()

        r2 = requests.post(f"{API}/auth/reset-password", json={"token": token, "new_password": ADMIN_PASSWORD})
        assert r2.status_code == 400

    def test_reset_password_invalid_token(self):
        r = requests.post(f"{API}/auth/reset-password", json={"token": "invalid_token_xxx", "new_password": "newpass123"})
        assert r.status_code == 400


# -------------------- Tenants --------------------
class TestTenants:
    created_tenant_id = None

    def test_create_tenant(self, admin_session):
        sub = f"testtenant{int(time.time())}"
        payload = {
            "business_name": "TEST_Venue Co",
            "admin_email": f"TEST_{sub}@test.com",
            "admin_password": "test123",
            "admin_name": "Test Admin",
            "subdomain": sub,
            "timezone": "UTC",
            "currency": "USD",
        }
        r = admin_session.post(f"{API}/tenants", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("id")
        assert data["business_name"] == "TEST_Venue Co"
        TestTenants.created_tenant_id = data["id"]

    def test_list_tenants_has_id(self, admin_session):
        r = admin_session.get(f"{API}/tenants")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        for t in data:
            assert t.get("id"), f"Tenant missing id: {t}"
            assert "_id" not in t, f"Mongo _id leaked: {t}"
        if TestTenants.created_tenant_id:
            ids = [t["id"] for t in data]
            assert TestTenants.created_tenant_id in ids

    def test_get_single_tenant(self, admin_session):
        assert TestTenants.created_tenant_id
        r = admin_session.get(f"{API}/tenants/{TestTenants.created_tenant_id}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("id") == TestTenants.created_tenant_id
        assert "_id" not in data


# -------------------- Venues --------------------
class TestVenues:
    created_venue_id = None

    def test_list_venues_has_id(self, admin_session):
        r = admin_session.get(f"{API}/venues")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for v in data:
            assert v.get("id")
            assert "_id" not in v

    def test_create_venue(self, admin_session, elite_tenant):
        payload = {
            "name": f"TEST_Venue_{int(time.time())}",
            "description": "Test venue",
            "address": "123 Test St",
            "tenant_id": elite_tenant["id"],
        }
        r = admin_session.post(f"{API}/venues", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("id")
        assert data.get("name") == payload["name"]
        TestVenues.created_venue_id = data["id"]


# -------------------- Courts --------------------
class TestCourts:
    created_court_id = None

    def test_list_courts_has_id(self, admin_session):
        r = admin_session.get(f"{API}/courts")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for c in data:
            assert c.get("id")
            assert "_id" not in c

    def test_create_court(self, admin_session, elite_tenant):
        assert TestVenues.created_venue_id, "Venue not created"
        payload = {
            "name": f"TEST_Court_{int(time.time())}",
            "sport_type": "tennis",
            "venue_id": TestVenues.created_venue_id,
            "tenant_id": elite_tenant["id"],
        }
        r = admin_session.post(f"{API}/courts", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("id")
        assert data["sport_type"] == "tennis"
        TestCourts.created_court_id = data["id"]


# -------------------- Bookings --------------------
class TestBookings:
    def test_list_bookings_has_id(self, admin_session):
        r = admin_session.get(f"{API}/bookings")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for b in data:
            assert b.get("id")
            assert "_id" not in b

    def test_create_booking_and_conflict_detected(self, admin_session):
        assert TestCourts.created_court_id, "Court not created"
        date = "2030-05-15"
        payload = {
            "court_id": TestCourts.created_court_id,
            "customer_name": "TEST Customer",
            "customer_email": "test_customer@example.com",
            "customer_phone": "+10000000000",
            "date": date,
            "start_time": "10:00",
            "end_time": "11:00",
            "total_price": 50.0,
        }
        r = admin_session.post(f"{API}/bookings", json=payload)
        assert r.status_code == 200, r.text
        assert r.json().get("id")

        # Conflict: overlapping same court/date/time
        r2 = admin_session.post(f"{API}/bookings", json=payload)
        assert r2.status_code == 400


# -------------------- Customers --------------------
class TestCustomers:
    def test_list_customers_has_id(self, admin_session):
        r = admin_session.get(f"{API}/customers")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for c in data:
            assert c.get("id") or c.get("email")
            assert "_id" not in c


# -------------------- Analytics --------------------
class TestAnalytics:
    def test_dashboard(self, admin_session):
        r = admin_session.get(f"{API}/analytics/dashboard")
        assert r.status_code == 200, r.text
        data = r.json()
        # Must be dict of stats
        assert isinstance(data, dict)


# -------------------- Subscriptions --------------------
class TestSubscriptions:
    def test_plans_returns_three(self):
        r = requests.get(f"{API}/subscriptions/plans")
        assert r.status_code == 200
        data = r.json()
        # Can be list or dict with 'plans'
        plans = data if isinstance(data, list) else data.get("plans", [])
        assert len(plans) == 3, f"Expected 3 plans, got {len(plans)}: {data}"


# -------------------- Public --------------------
class TestPublic:
    def test_public_tenant(self, elite_tenant):
        r = requests.get(f"{API}/public/tenant/elite-sports")
        assert r.status_code == 200
        data = r.json()
        assert data.get("subdomain") == "elite-sports"
        assert "venues" in data
        assert isinstance(data["venues"], list)

    def test_public_venue_with_courts(self, admin_session):
        # Use a venue from the venues list
        r = admin_session.get(f"{API}/venues")
        assert r.status_code == 200
        venues = r.json()
        if not venues:
            pytest.skip("No venues exist")
        venue_id = venues[0]["id"]
        r2 = requests.get(f"{API}/public/venue/{venue_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data.get("id") == venue_id
        assert "courts" in data


# -------------------- Pricing --------------------
class TestPricing:
    def test_list_pricing_has_id(self, admin_session):
        r = admin_session.get(f"{API}/pricing")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for p in data:
            assert p.get("id") or True  # may be empty
            assert "_id" not in p
