"""Tests for (1) super_admin global view on /courts, /customers, /pricing
and (2) FastAPI lifespan migration (indexes + seed admin)."""
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
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017").strip().strip('"')
DB_NAME = os.environ.get("DB_NAME", "spancle_db").strip().strip('"')
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

ADMIN_EMAIL = "admin@spancle.com"
ADMIN_PASSWORD = "admin123"
TENANT_EMAIL = "elite@test.com"
TENANT_PASSWORD = "test123"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def admin_session():
    db.login_attempts.delete_many({})
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def tenant_session():
    db.login_attempts.delete_many({})
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": TENANT_EMAIL, "password": TENANT_PASSWORD})
    assert r.status_code == 200, f"tenant login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def elite_tenant_id(admin_session):
    r = admin_session.get(f"{API}/tenants")
    assert r.status_code == 200
    for t in r.json():
        if t.get("subdomain") == "elite-sports":
            return t["id"]
    pytest.skip("Elite Sports tenant does not exist")


@pytest.fixture(scope="module")
def seeded_cross_tenant_court(admin_session):
    """Ensure there's at least 1 court under a *different* tenant so super_admin
    can observe aggregation across multiple tenants."""
    # Use or create a second tenant
    sub = f"testsuper{int(time.time())}"
    payload = {
        "business_name": "TEST_Super View Co",
        "admin_email": f"TEST_{sub}@test.com",
        "admin_password": "test123",
        "admin_name": "T",
        "subdomain": sub,
        "timezone": "UTC",
        "currency": "USD",
    }
    r = admin_session.post(f"{API}/tenants", json=payload)
    assert r.status_code == 200, r.text
    t2 = r.json()
    tenant2_id = t2["id"]

    # Create venue
    r = admin_session.post(
        f"{API}/venues",
        json={"name": f"TEST_V_{sub}", "description": "d", "address": "a", "tenant_id": tenant2_id},
    )
    assert r.status_code == 200, r.text
    venue2_id = r.json()["id"]

    # Create court
    r = admin_session.post(
        f"{API}/courts",
        json={
            "name": f"TEST_Court_{sub}",
            "sport_type": "badminton",
            "venue_id": venue2_id,
            "tenant_id": tenant2_id,
        },
    )
    assert r.status_code == 200, r.text
    return {"tenant_id": tenant2_id, "venue_id": venue2_id, "court_id": r.json()["id"]}


# ---------- Super admin global view tests ----------
class TestSuperAdminGlobalView:
    def test_courts_global_view_aggregates_all_tenants(
        self, admin_session, elite_tenant_id, seeded_cross_tenant_court
    ):
        r = admin_session.get(f"{API}/courts")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 2, f"Expected courts from >=2 tenants, got {len(data)}"
        tenant_ids = {c.get("tenant_id") for c in data}
        assert elite_tenant_id in tenant_ids, "Elite court missing from global view"
        assert seeded_cross_tenant_court["tenant_id"] in tenant_ids, "Second tenant court missing"
        for c in data:
            assert "_id" not in c
            assert c.get("id")

    def test_courts_with_tenant_id_filter(self, admin_session, elite_tenant_id):
        r = admin_session.get(f"{API}/courts", params={"tenant_id": elite_tenant_id})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for c in data:
            assert c.get("tenant_id") == elite_tenant_id, f"Leak: {c}"

    def test_customers_global_view_no_error(self, admin_session):
        r = admin_session.get(f"{API}/customers")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for c in data:
            assert "_id" not in c

    def test_customers_with_tenant_id_filter(self, admin_session, elite_tenant_id):
        r = admin_session.get(f"{API}/customers", params={"tenant_id": elite_tenant_id})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_pricing_global_view_no_error(self, admin_session):
        r = admin_session.get(f"{API}/pricing")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for p in data:
            assert "_id" not in p

    def test_pricing_with_tenant_id_filter(self, admin_session, elite_tenant_id):
        r = admin_session.get(f"{API}/pricing", params={"tenant_id": elite_tenant_id})
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- Tenant admin scoping (regression) ----------
class TestTenantAdminScoping:
    def test_tenant_admin_courts_only_own_tenant(
        self, tenant_session, elite_tenant_id, seeded_cross_tenant_court
    ):
        r = tenant_session.get(f"{API}/courts")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for c in data:
            assert c.get("tenant_id") == elite_tenant_id, f"Tenant leak: {c}"
        other_ids = [c["id"] for c in data if c["id"] == seeded_cross_tenant_court["court_id"]]
        assert not other_ids, "Tenant admin saw another tenant's court"

    def test_tenant_admin_customers_only_own_tenant(self, tenant_session, elite_tenant_id):
        r = tenant_session.get(f"{API}/customers")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for c in data:
            assert c.get("tenant_id") == elite_tenant_id, f"Tenant leak: {c}"

    def test_tenant_admin_cannot_bypass_with_query_param(
        self, tenant_session, seeded_cross_tenant_court
    ):
        """Even if tenant_admin passes ?tenant_id=<other>, backend should still scope
        to their own tenant (current impl ignores param for non-super_admin)."""
        r = tenant_session.get(
            f"{API}/courts", params={"tenant_id": seeded_cross_tenant_court["tenant_id"]}
        )
        assert r.status_code == 200
        for c in r.json():
            assert c.get("tenant_id") != seeded_cross_tenant_court["tenant_id"], (
                "Tenant admin bypassed scoping via query param!"
            )


# ---------- Lifespan migration (startup) ----------
class TestLifespanStartup:
    def test_users_email_unique_index_exists(self):
        idx = db.users.index_information()
        email_idx = [v for k, v in idx.items() if any("email" == f[0] for f in v.get("key", []))]
        assert email_idx, f"users.email index missing. Have: {list(idx.keys())}"
        assert any(i.get("unique") for i in email_idx), "users.email index not unique"

    def test_tenants_subdomain_unique_index_exists(self):
        idx = db.tenants.index_information()
        sub_idx = [v for k, v in idx.items() if any("subdomain" == f[0] for f in v.get("key", []))]
        assert sub_idx, f"tenants.subdomain index missing. Have: {list(idx.keys())}"
        assert any(i.get("unique") for i in sub_idx), "tenants.subdomain index not unique"

    def test_password_reset_ttl_index_exists(self):
        idx = db.password_reset_tokens.index_information()
        ttl_idx = [v for v in idx.values() if "expireAfterSeconds" in v]
        assert ttl_idx, "password_reset_tokens TTL index missing"

    def test_admin_seeded_and_can_login(self):
        admin = db.users.find_one({"email": ADMIN_EMAIL})
        assert admin is not None, "super_admin not seeded"
        assert admin.get("role") == "super_admin"
        assert admin.get("password_hash", "").startswith("$2b$"), "bcrypt hash invalid"
        db.login_attempts.delete_many({})
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200


# ---------- Regression smoke ----------
class TestRegressionSmoke:
    def test_register_tenant_still_works(self):
        sub = f"testlife{int(time.time())}"
        r = requests.post(
            f"{API}/auth/register-tenant",
            json={
                "name": "TEST_Life",
                "email": f"TEST_life_{sub}@example.com",
                "password": "test123",
                "business_name": "TEST Life Co",
                "subdomain": sub,
            },
        )
        assert r.status_code == 200, r.text
        assert r.json().get("role") == "tenant_admin"

    def test_forgot_password_works(self):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": ADMIN_EMAIL})
        assert r.status_code == 200

    def test_tenants_list_works(self, admin_session):
        r = admin_session.get(f"{API}/tenants")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_venues_list_works(self, admin_session):
        r = admin_session.get(f"{API}/venues")
        assert r.status_code == 200

    def test_bookings_list_works(self, admin_session):
        r = admin_session.get(f"{API}/bookings")
        assert r.status_code == 200


# ---------- Cleanup ----------
@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    # Cleanup TEST_ tenants, their users, venues, courts
    for t in db.tenants.find({"business_name": {"$regex": "^TEST"}}):
        tid = str(t["_id"])
        db.venues.delete_many({"tenant_id": tid})
        db.courts.delete_many({"tenant_id": tid})
        db.users.delete_many({"tenant_id": tid})
    db.tenants.delete_many({"business_name": {"$regex": "^TEST"}})
    db.users.delete_many({"email": {"$regex": "^TEST_"}})
    db.login_attempts.delete_many({})
