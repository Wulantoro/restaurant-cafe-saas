import uuid
import pytest
from sqlalchemy import text
from app.core.database import engine


@pytest.fixture(scope="module", autouse=True)
def clean_database():
    """Ensure database is clean before running Phase 1 test suite."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE audit_logs CASCADE;"))
        conn.execute(text("TRUNCATE TABLE user_outlet_roles CASCADE;"))
        conn.execute(text("TRUNCATE TABLE users CASCADE;"))
        conn.execute(text("TRUNCATE TABLE outlets CASCADE;"))
        conn.execute(text("TRUNCATE TABLE tenants CASCADE;"))
    yield


def test_business_registration_success(client):
    """FR-001, FR-002: Verify new business registration creates tenant, outlet, and owner."""
    payload = {
        "business_name": "Kopi Nusantara Group",
        "owner_full_name": "Budi Santoso",
        "owner_email": "budi@kopinusantara.com",
        "owner_password": "SecurePassword123!",
        "initial_outlet_name": "Kopi Nusantara Senopati",
        "initial_outlet_address": "Jl. Senopati No. 45, Jakarta",
        "initial_outlet_payment_timing": "PAY_AFTER_SERVING",
    }
    res = client.post("/api/v1/auth/register-business", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

    user = data["data"]["user"]
    assert user["email"] == "budi@kopinusantara.com"
    assert user["is_owner"] is True
    assert user["is_central_admin"] is True
    assert user["is_active"] is True


def test_business_registration_validation(client):
    """NFR-006: Input validation checks on business registration."""
    # Invalid password (less than 8 chars)
    payload = {
        "business_name": "Warung Kopi",
        "owner_full_name": "Joko",
        "owner_email": "joko@warung.com",
        "owner_password": "short",
        "initial_outlet_name": "Outlet 1",
    }
    res = client.post("/api/v1/auth/register-business", json=payload)
    assert res.status_code == 422
    assert res.json()["status"] == "error"
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_success_and_failure(client):
    """FR-008: Verify authentication credentials, token generation, and rejection."""
    # 1. Successful login
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "SecurePassword123!"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "access_token" in data
    assert data["user"]["email"] == "budi@kopinusantara.com"

    # 2. Invalid password
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    assert res.json()["status"] == "error"
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # 3. Non-existent email
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@kopinusantara.com", "password": "AnyPassword123!"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_auth_me_endpoint(client):
    """FR-008: Verify /auth/me returns profile, tenant details, and outlet access."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "SecurePassword123!"},
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    me = res.json()["data"]
    assert me["email"] == "budi@kopinusantara.com"
    assert me["tenant_name"] == "Kopi Nusantara Group"
    assert me["is_owner"] is True
    assert len(me["outlets"]) >= 1
    assert me["outlets"][0]["outlet_name"] == "Kopi Nusantara Senopati"
    assert "OWNER" in me["outlets"][0]["roles"]


def test_tenant_settings_and_audit_logging(client):
    """FR-003, BR-016, BR-027: Update central settings, negative inventory policy, and audit log."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "SecurePassword123!"},
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update tax_rate and service_charge_rate
    res = client.patch(
        "/api/v1/tenant/settings",
        headers=headers,
        json={"tax_rate": 11.0, "service_charge_rate": 5.0},
    )
    assert res.status_code == 200
    tenant_data = res.json()["data"]
    assert float(tenant_data["tax_rate"]) == 11.0
    assert float(tenant_data["service_charge_rate"]) == 5.0

    # 2. Owner toggles allow_negative_inventory (BR-016)
    res = client.patch(
        "/api/v1/tenants/me",
        headers=headers,
        json={
            "allow_negative_inventory": True,
            "reason": "Peak holiday season inventory policy",
        },
    )
    assert res.status_code == 200
    assert res.json()["data"]["allow_negative_inventory"] is True

    # 3. Verify audit log was recorded for negative inventory policy change
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT action, entity_type, new_values, reason FROM audit_logs WHERE action = 'UPDATE_NEGATIVE_INVENTORY_POLICY'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "UPDATE_NEGATIVE_INVENTORY_POLICY"
        assert row[1] == "TENANT"
        assert row[2]["allow_negative_inventory"] is True
        assert "Peak holiday season" in row[3]


def test_outlet_management(client):
    """FR-004, FR-005, FR-006, BR-008: Multi-outlet creation, listing, and updates."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "SecurePassword123!"},
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create second outlet
    outlet_payload = {
        "name": "Kopi Nusantara Kemang",
        "address": "Jl. Kemang Raya No. 12, Jakarta",
        "payment_timing": "PAY_BEFORE_SERVING",
    }
    res = client.post("/api/v1/outlets", headers=headers, json=outlet_payload)
    assert res.status_code == 201
    second_outlet = res.json()["data"]
    assert second_outlet["name"] == "Kopi Nusantara Kemang"
    assert second_outlet["payment_timing"] == "PAY_BEFORE_SERVING"

    # 2. List outlets
    res = client.get("/api/v1/outlets", headers=headers)
    assert res.status_code == 200
    outlets = res.json()["data"]
    assert len(outlets) == 2

    # 3. Get outlet by ID
    res = client.get(f"/api/v1/outlets/{second_outlet['id']}", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Kopi Nusantara Kemang"

    # 4. Update outlet
    res = client.patch(
        f"/api/v1/outlets/{second_outlet['id']}",
        headers=headers,
        json={"name": "Kopi Nusantara Kemang Flagship", "payment_timing": "PAY_AFTER_SERVING"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Kopi Nusantara Kemang Flagship"
    assert res.json()["data"]["payment_timing"] == "PAY_AFTER_SERVING"


def test_employee_and_role_management(client):
    """FR-010, FR-011, FR-013, FR-014: Employee creation, multi-role assignment, and deactivation."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "SecurePassword123!"},
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch an outlet id
    outlets_res = client.get("/api/v1/outlets", headers=headers)
    outlet_id = outlets_res.json()["data"][0]["id"]

    # 1. Create Employee (Waiter)
    emp_payload = {
        "full_name": "Dewi Sartika",
        "email": "dewi@kopinusantara.com",
        "password": "PasswordDewi123!",
        "is_central_admin": False,
        "initial_outlet_id": outlet_id,
        "initial_role": "WAITER",
    }
    res = client.post("/api/v1/users", headers=headers, json=emp_payload)
    assert res.status_code == 201
    dewi = res.json()["data"]
    dewi_id = dewi["id"]
    assert dewi["email"] == "dewi@kopinusantara.com"

    # 2. Assign second role (CASHIER) to Dewi for same outlet (FR-011: Multi-role support)
    role_payload = {"outlet_id": outlet_id, "role": "CASHIER"}
    res = client.post(f"/api/v1/users/{dewi_id}/roles", headers=headers, json=role_payload)
    assert res.status_code == 201
    assert res.json()["data"]["role"] == "CASHIER"
    cashier_role_id = res.json()["data"]["id"]

    # 3. Verify audit log captured the role assignment
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT action, entity_type FROM audit_logs WHERE action = 'ASSIGN_OUTLET_ROLE' AND entity_id = '{cashier_role_id}'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "ASSIGN_OUTLET_ROLE"

    # 4. Dewi logs in successfully
    dewi_login = client.post(
        "/api/v1/auth/login",
        json={"email": "dewi@kopinusantara.com", "password": "PasswordDewi123!"},
    )
    assert dewi_login.status_code == 200
    dewi_token = dewi_login.json()["data"]["access_token"]

    # 5. Check Dewi's /auth/me returns both WAITER and CASHIER roles
    dewi_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {dewi_token}"})
    assert dewi_me.status_code == 200
    assigned_roles = dewi_me.json()["data"]["outlets"][0]["roles"]
    assert "WAITER" in assigned_roles
    assert "CASHIER" in assigned_roles

    # 6. Deactivate Dewi's account (FR-014)
    res = client.patch(
        f"/api/v1/users/{dewi_id}",
        headers=headers,
        json={"is_active": False, "reason": "Employee resigned"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_active"] is False

    # 7. Dewi cannot log in while inactive
    dewi_login_after = client.post(
        "/api/v1/auth/login",
        json={"email": "dewi@kopinusantara.com", "password": "PasswordDewi123!"},
    )
    assert dewi_login_after.status_code == 403
    assert dewi_login_after.json()["error"]["code"] == "USER_INACTIVE"

    # 8. Reactivate Dewi
    client.patch(f"/api/v1/users/{dewi_id}", headers=headers, json={"is_active": True})
    dewi_login_reactivated = client.post(
        "/api/v1/auth/login",
        json={"email": "dewi@kopinusantara.com", "password": "PasswordDewi123!"},
    )
    assert dewi_login_reactivated.status_code == 200


def test_cross_tenant_data_isolation(client):
    """BR-001, NFR-003: Strict multi-tenant isolation prevents cross-tenant access."""
    # 1. Register Business B
    biz_b_payload = {
        "business_name": "Roti Bakar Nusantara",
        "owner_full_name": "Rudi Hartono",
        "owner_email": "rudi@rotibakar.com",
        "owner_password": "RudiPassword123!",
        "initial_outlet_name": "Roti Bakar Tebet",
        "initial_outlet_payment_timing": "PAY_BEFORE_SERVING",
    }
    res = client.post("/api/v1/auth/register-business", json=biz_b_payload)
    assert res.status_code == 201
    rudi_token = res.json()["data"]["access_token"]
    rudi_headers = {"Authorization": f"Bearer {rudi_token}"}

    # Get Tenant A (Kopi Nusantara) owner token and outlet
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "SecurePassword123!"},
    )
    budi_token = login_a.json()["data"]["access_token"]
    budi_headers = {"Authorization": f"Bearer {budi_token}"}
    outlets_a = client.get("/api/v1/outlets", headers=budi_headers).json()["data"]
    outlet_a_id = outlets_a[0]["id"]

    # 2. Tenant B owner attempts to view Tenant A's outlet -> 404 OUTLET_NOT_FOUND
    cross_res = client.get(f"/api/v1/outlets/{outlet_a_id}", headers=rudi_headers)
    assert cross_res.status_code == 404
    assert cross_res.json()["error"]["code"] == "OUTLET_NOT_FOUND"

    # 3. Tenant B owner attempts to update Tenant A's outlet -> 404 OUTLET_NOT_FOUND
    cross_patch = client.patch(
        f"/api/v1/outlets/{outlet_a_id}",
        headers=rudi_headers,
        json={"name": "Hacked Outlet Name"},
    )
    assert cross_patch.status_code == 404
    assert cross_patch.json()["error"]["code"] == "OUTLET_NOT_FOUND"

    # 4. Tenant B lists outlets: sees only Tenant B's outlets (1 outlet), never Tenant A
    list_b = client.get("/api/v1/outlets", headers=rudi_headers)
    assert list_b.status_code == 200
    assert len(list_b.json()["data"]) == 1
    assert list_b.json()["data"][0]["name"] == "Roti Bakar Tebet"

    # 5. Tenant B owner attempts to view Tenant A's employee -> 404 USER_NOT_FOUND
    budi_id = login_a.json()["data"]["user"]["id"]
    cross_user = client.get(f"/api/v1/users/{budi_id}", headers=rudi_headers)
    assert cross_user.status_code == 404
    assert cross_user.json()["error"]["code"] == "USER_NOT_FOUND"

    # 6. Tenant B owner attempts to assign role to Tenant A's user -> 404 USER_NOT_FOUND
    outlet_b_id = list_b.json()["data"][0]["id"]
    cross_role = client.post(
        f"/api/v1/users/{budi_id}/roles",
        headers=rudi_headers,
        json={"outlet_id": outlet_b_id, "role": "MANAGER"},
    )
    assert cross_role.status_code == 404
    assert cross_role.json()["error"]["code"] == "USER_NOT_FOUND"


def test_unauthorized_role_rejection(client):
    """NFR-004, BD-001: Operational staff denied admin operations; non-owner denied owner actions."""
    # 1. Login as Dewi (staff in Tenant A)
    dewi_login = client.post(
        "/api/v1/auth/login",
        json={"email": "dewi@kopinusantara.com", "password": "PasswordDewi123!"},
    )
    dewi_token = dewi_login.json()["data"]["access_token"]
    dewi_headers = {"Authorization": f"Bearer {dewi_token}"}

    # 2. Dewi attempts to create outlet -> 403 FORBIDDEN
    res = client.post(
        "/api/v1/outlets",
        headers=dewi_headers,
        json={"name": "Unauthorized Outlet", "payment_timing": "PAY_BEFORE_SERVING"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

    # 3. Dewi attempts to update central tenant settings -> 403 FORBIDDEN
    res = client.patch(
        "/api/v1/tenant/settings",
        headers=dewi_headers,
        json={"tax_rate": 20.0},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

    # 4. Dewi attempts to register a new employee -> 403 FORBIDDEN
    res = client.post(
        "/api/v1/users",
        headers=dewi_headers,
        json={
            "full_name": "Ronggo",
            "email": "ronggo@kopinusantara.com",
            "password": "PasswordRonggo123!",
        },
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

    # 5. Create a Central Admin user (non-owner) in Tenant A
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@kopinusantara.com", "password": "SecurePassword123!"},
    )
    budi_headers = {"Authorization": f"Bearer {login_a.json()['data']['access_token']}"}

    res = client.post(
        "/api/v1/users",
        headers=budi_headers,
        json={
            "full_name": "Citra Admin",
            "email": "citra@kopinusantara.com",
            "password": "PasswordCitra123!",
            "is_central_admin": True,
        },
    )
    assert res.status_code == 201

    citra_login = client.post(
        "/api/v1/auth/login",
        json={"email": "citra@kopinusantara.com", "password": "PasswordCitra123!"},
    )
    citra_headers = {"Authorization": f"Bearer {citra_login.json()['data']['access_token']}"}

    # 6. Central Admin CAN update tax_rate (Centralized Governance BD-001)
    res = client.patch(
        "/api/v1/tenant/settings",
        headers=citra_headers,
        json={"tax_rate": 10.0},
    )
    assert res.status_code == 200
    assert float(res.json()["data"]["tax_rate"]) == 10.0

    # 7. Central Admin CANNOT update allow_negative_inventory (Owner Only, BR-016)
    res = client.patch(
        "/api/v1/tenant/settings",
        headers=citra_headers,
        json={"allow_negative_inventory": False},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

    # 8. Central Admin CANNOT grant is_central_admin to another user (Owner Only, BD-001)
    res = client.post(
        "/api/v1/users",
        headers=citra_headers,
        json={
            "full_name": "Eko Sub-Admin",
            "email": "eko@kopinusantara.com",
            "password": "PasswordEko123!",
            "is_central_admin": True,
        },
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"
