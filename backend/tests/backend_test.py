"""Backend tests for Spancle - focused on login, tenants, venues, courts, forgot/reset password."""
import os
import pytest
import requests
from pymongo import MongoClient
from bson import ObjectId

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tenant-cloud-builder.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

# Mongo direct access for token retrieval
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'spancle_db')
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

ADMIN_EMAIL = "admin@spancle.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "id" in data and "email" in data and "role" in data
    assert data["role"] == "super_admin"
    return s


# ---------- Auth ----------
class TestAuth:
    def test_login_success(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "super_admin"
        assert data["id"]

    def test_login_invalid(self):
        # Use a unique email to avoid lockout polluting admin login (backend locks after 1 fail bug)
        r = requests.post(f"{API}/auth/login", json={"email": "nobody_xyz@test.com", "password": "wrong"})
        assert r.status_code in (401, 429)
        # Cleanup the lockout record to not affect subsequent tests
        db.login_attempts.delete_many({})


# ---------- Forgot / Reset Password ----------
class TestForgotReset:
    def test_forgot_password_valid_email(self):
        # Clean up old tokens
        db.password_reset_tokens.delete_many({"email": ADMIN_EMAIL})
        r = requests.post(f"{API}/auth/forgot-password", json={"email": ADMIN_EMAIL})
        assert r.status_code == 200
        assert "message" in r.json()
        # Token should exist in DB
        token_doc = db.password_reset_tokens.find_one({"email": ADMIN_EMAIL, "used": False})
        assert token_doc is not None
        assert token_doc.get("token")

    def test_forgot_password_invalid_email_no_enumeration(self):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": "nosuchuser_xyz@example.com"})
        assert r.status_code == 200
        assert "message" in r.json()

    def test_reset_password_and_reuse_blocked(self, admin_session):
        # Request a fresh token
        db.password_reset_tokens.delete_many({"email": ADMIN_EMAIL})
        r = requests.post(f"{API}/auth/forgot-password", json={"email": ADMIN_EMAIL})
        assert r.status_code == 200
        token_doc = db.password_reset_tokens.find_one({"email": ADMIN_EMAIL, "used": False})
        assert token_doc is not None
        token = token_doc["token"]

        # Reset password to same value (so subsequent tests keep working)
        r = requests.post(f"{API}/auth/reset-password", json={"token": token, "new_password": ADMIN_PASSWORD})
        assert r.status_code == 200
        assert "message" in r.json()

        # Reuse the same token -> should fail
        r2 = requests.post(f"{API}/auth/reset-password", json={"token": token, "new_password": ADMIN_PASSWORD})
        assert r2.status_code == 400

    def test_reset_password_invalid_token(self):
        r = requests.post(f"{API}/auth/reset-password", json={"token": "invalid_token_xxx", "new_password": "newpass123"})
        assert r.status_code == 400


# ---------- Tenants ----------
class TestTenants:
    created_tenant_id = None

    def test_create_tenant(self, admin_session):
        import time
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
        assert isinstance(data, list)
        assert len(data) > 0
        for t in data:
            assert t.get("id"), f"Tenant missing id: {t}"
            assert "_id" not in t, f"Mongo _id leaked: {t}"
        # Newly created tenant must be present
        if TestTenants.created_tenant_id:
            ids = [t["id"] for t in data]
            assert TestTenants.created_tenant_id in ids


# ---------- Venues ----------
class TestVenues:
    def test_list_venues_has_id(self, admin_session):
        r = admin_session.get(f"{API}/venues")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for v in data:
            assert v.get("id")
            assert "_id" not in v


# ---------- Courts ----------
class TestCourts:
    def test_list_courts_has_id(self, admin_session):
        r = admin_session.get(f"{API}/courts")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for c in data:
            assert c.get("id")
            assert "_id" not in c
