"""Tests for POST /api/auth/register-tenant (self-serve tenant registration)."""
import os
import time
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").strip().rstrip("/")
API = f"{BASE_URL}/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017").strip().strip('"')
DB_NAME = os.environ.get("DB_NAME", "spancle_db").strip().strip('"')
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@spancle.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# unique per-run identifiers
TS = int(time.time())
TEST_EMAIL = f"test_tenant_reg_{TS}@example.com"
TEST_SUBDOMAIN = f"testreg{TS}"
TEST_BUSINESS = f"TEST_RegBiz_{TS}"


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    # Ensure nothing leftover prior
    db.users.delete_many({"email": {"$regex": "^test_tenant_reg_"}})
    db.tenants.delete_many({"subdomain": {"$regex": "^testreg"}})
    db.login_attempts.delete_many({})
    yield
    db.users.delete_many({"email": {"$regex": "^test_tenant_reg_"}})
    db.tenants.delete_many({"subdomain": {"$regex": "^testreg"}})


class TestRegisterTenant:
    created_tenant_id = None
    created_user_id = None

    def test_register_tenant_success(self):
        payload = {
            "name": "Reg Tester",
            "email": TEST_EMAIL,
            "password": "testpass123",
            "business_name": TEST_BUSINESS,
            "subdomain": TEST_SUBDOMAIN,
        }
        r = requests.post(f"{API}/auth/register-tenant", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == TEST_EMAIL
        assert data["name"] == "Reg Tester"
        assert data["role"] == "tenant_admin"
        assert data["tenant_id"]
        assert data["id"]
        # Cookies set on response
        cookie_names = {c.name for c in r.cookies}
        assert "access_token" in cookie_names, f"cookies: {cookie_names}"

        TestRegisterTenant.created_tenant_id = data["tenant_id"]
        TestRegisterTenant.created_user_id = data["id"]

    def test_duplicate_email_returns_400(self):
        payload = {
            "name": "Dup Email",
            "email": TEST_EMAIL,  # same email
            "password": "testpass123",
            "business_name": "Some Other Biz",
            "subdomain": f"{TEST_SUBDOMAIN}x",
        }
        r = requests.post(f"{API}/auth/register-tenant", json=payload)
        assert r.status_code == 400, r.text
        assert "Email already registered" in r.json().get("detail", "")

    def test_duplicate_subdomain_returns_400(self):
        payload = {
            "name": "Dup Sub",
            "email": f"other_test_tenant_reg_{TS}@example.com",
            "password": "testpass123",
            "business_name": "Another Biz",
            "subdomain": TEST_SUBDOMAIN,  # same subdomain
        }
        r = requests.post(f"{API}/auth/register-tenant", json=payload)
        assert r.status_code == 400, r.text
        assert "Subdomain already taken" in r.json().get("detail", "")
        # cleanup user if created (shouldn't be)
        db.users.delete_one({"email": payload["email"]})

    def test_new_tenant_visible_to_super_admin(self):
        assert TestRegisterTenant.created_tenant_id
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200, r.text
        r2 = s.get(f"{API}/tenants")
        assert r2.status_code == 200
        tenants = r2.json()
        match = [t for t in tenants if t.get("id") == TestRegisterTenant.created_tenant_id]
        assert match, f"New tenant {TestRegisterTenant.created_tenant_id} not in tenant list"
        t = match[0]
        assert t.get("business_name") == TEST_BUSINESS
        assert t.get("subdomain") == TEST_SUBDOMAIN
        assert "_id" not in t

    def test_new_user_can_login_and_me_returns_tenant_admin(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": "testpass123"})
        assert r.status_code == 200, r.text
        login_data = r.json()
        assert login_data["role"] == "tenant_admin"
        assert login_data["tenant_id"] == TestRegisterTenant.created_tenant_id

        r2 = s.get(f"{API}/auth/me")
        assert r2.status_code == 200
        me = r2.json()
        assert me.get("role") == "tenant_admin"
        assert me.get("tenant_id") == TestRegisterTenant.created_tenant_id
        assert me.get("email") == TEST_EMAIL
