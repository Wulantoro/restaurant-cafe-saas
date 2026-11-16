import uuid
from decimal import Decimal
import pytest
from sqlalchemy import text
from app.core.database import engine


@pytest.fixture(scope="module", autouse=True)
def clean_database():
    """Ensure database is clean before running Phase 2 test suite."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE audit_logs CASCADE;"))
        conn.execute(text("TRUNCATE TABLE recipe_items CASCADE;"))
        conn.execute(text("TRUNCATE TABLE inventory_balances CASCADE;"))
        conn.execute(text("TRUNCATE TABLE ingredients CASCADE;"))
        conn.execute(text("TRUNCATE TABLE outlet_product_availability CASCADE;"))
        conn.execute(text("TRUNCATE TABLE product_addons CASCADE;"))
        conn.execute(text("TRUNCATE TABLE product_variants CASCADE;"))
        conn.execute(text("TRUNCATE TABLE products CASCADE;"))
        conn.execute(text("TRUNCATE TABLE menu_categories CASCADE;"))
        conn.execute(text("TRUNCATE TABLE user_outlet_roles CASCADE;"))
        conn.execute(text("TRUNCATE TABLE users CASCADE;"))
        conn.execute(text("TRUNCATE TABLE outlets CASCADE;"))
        conn.execute(text("TRUNCATE TABLE tenants CASCADE;"))
    yield


@pytest.fixture(scope="module")
def setup_tenants(client):
    """Register Tenant A and Tenant B for testing catalog isolation and role policies."""
    # 1. Register Tenant A (Kopi Maju)
    res_a = client.post(
        "/api/v1/auth/register-business",
        json={
            "business_name": "Kopi Maju Utama",
            "owner_full_name": "Alice Wijaya",
            "owner_email": "alice@kopimaju.com",
            "owner_password": "Password123!",
            "initial_outlet_name": "Kopi Maju Kebayoran",
            "initial_outlet_address": "Jl. Gandaria 1",
            "initial_outlet_payment_timing": "PAY_BEFORE_SERVING",
        },
    )
    assert res_a.status_code == 201, res_a.text
    data_a = res_a.json()["data"]
    token_a = data_a["access_token"]
    user_a = data_a["user"]
    tenant_a_id = user_a["tenant_id"]

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Fetch outlets of Tenant A
    outlets_res = client.get("/api/v1/outlets", headers=headers_a)
    assert outlets_res.status_code == 200
    outlet_a1_id = outlets_res.json()["data"][0]["id"]

    # Create second outlet for Tenant A
    res_a2 = client.post(
        "/api/v1/outlets",
        headers=headers_a,
        json={
            "name": "Kopi Maju Kemang",
            "address": "Jl. Kemang Raya 10",
            "payment_timing": "PAY_AFTER_SERVING",
        },
    )
    assert res_a2.status_code == 201
    outlet_a2_id = res_a2.json()["data"]["id"]

    # Create Waiter employee in Tenant A (outlet-scoped, non-central-admin)
    emp_res = client.post(
        "/api/v1/employees",
        headers=headers_a,
        json={
            "full_name": "Bob Waiter",
            "email": "bob.waiter@kopimaju.com",
            "password": "Password123!",
            "is_central_admin": False,
        },
    )
    assert emp_res.status_code == 201
    waiter_user_id = emp_res.json()["data"]["id"]

    # Assign WAITER role to Bob for outlet A1
    role_res = client.post(
        f"/api/v1/users/{waiter_user_id}/roles",
        headers=headers_a,
        json={"outlet_id": outlet_a1_id, "role": "WAITER"},
    )
    assert role_res.status_code == 201

    # Login as Waiter
    login_bob = client.post(
        "/api/v1/auth/login",
        json={"email": "bob.waiter@kopimaju.com", "password": "Password123!"},
    )
    assert login_bob.status_code == 200
    token_bob = login_bob.json()["data"]["access_token"]
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    # 2. Register Tenant B (Burger Star)
    res_b = client.post(
        "/api/v1/auth/register-business",
        json={
            "business_name": "Burger Star Group",
            "owner_full_name": "Charlie Chaplin",
            "owner_email": "charlie@burgerstar.com",
            "owner_password": "Password123!",
            "initial_outlet_name": "Burger Star Sudirman",
        },
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    outlets_b = client.get("/api/v1/outlets", headers=headers_b).json()["data"]
    outlet_b1_id = outlets_b[0]["id"]

    return {
        "tenant_a_id": tenant_a_id,
        "token_a": token_a,
        "headers_a": headers_a,
        "outlet_a1_id": outlet_a1_id,
        "outlet_a2_id": outlet_a2_id,
        "waiter_headers": headers_bob,
        "headers_b": headers_b,
        "outlet_b1_id": outlet_b1_id,
    }


def test_category_crud_and_validation(client, setup_tenants):
    """FR-016: Centralized category CRUD, duplicate prevention, and listing."""
    headers_a = setup_tenants["headers_a"]

    # 1. Create Category "Coffee & Beverages"
    cat_payload = {
        "name": "Coffee & Beverages",
        "sort_order": 1,
    }
    res = client.post("/api/v1/catalog/categories", headers=headers_a, json=cat_payload)
    assert res.status_code == 201
    cat_data = res.json()["data"]
    assert cat_data["name"] == "Coffee & Beverages"
    assert cat_data["sort_order"] == 1
    cat_id = cat_data["id"]

    # 2. Duplicate category name rejected
    dup_res = client.post("/api/v1/catalog/categories", headers=headers_a, json=cat_payload)
    assert dup_res.status_code == 400
    assert dup_res.json()["error"]["code"] == "DUPLICATE_CATEGORY"

    # 3. Create second category
    res2 = client.post(
        "/api/v1/catalog/categories",
        headers=headers_a,
        json={"name": "Pastries & Bakeries", "sort_order": 2},
    )
    assert res2.status_code == 201

    # 4. List categories
    list_res = client.get("/api/v1/catalog/categories", headers=headers_a)
    assert list_res.status_code == 200
    categories = list_res.json()["data"]
    assert len(categories) == 2
    assert categories[0]["name"] == "Coffee & Beverages"

    # 5. Get single category
    get_res = client.get(f"/api/v1/catalog/categories/{cat_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == cat_id

    # 6. Update category
    patch_res = client.patch(
        f"/api/v1/catalog/categories/{cat_id}",
        headers=headers_a,
        json={"name": "Specialty Coffee & Beverages", "sort_order": 5},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["name"] == "Specialty Coffee & Beverages"
    assert patch_res.json()["data"]["sort_order"] == 5


def test_ingredient_creation_and_balance_initialization(client, setup_tenants):
    """FR-063: Central ingredient management and automated inventory balance initialization."""
    headers_a = setup_tenants["headers_a"]

    # 1. Create Ingredient "Arabica Coffee Beans"
    ing_payload = {
        "name": "Arabica Coffee Beans",
        "unit": "G",
        "min_stock_threshold": 500.0,
        "average_unit_cost": 150.0,
    }
    res = client.post("/api/v1/inventory/ingredients", headers=headers_a, json=ing_payload)
    assert res.status_code == 201
    ing1 = res.json()["data"]
    assert ing1["name"] == "Arabica Coffee Beans"
    assert ing1["unit"] == "G"
    assert float(ing1["average_unit_cost"]) == 150.0
    ing1_id = ing1["id"]

    # 2. Duplicate ingredient rejected
    dup_res = client.post("/api/v1/inventory/ingredients", headers=headers_a, json=ing_payload)
    assert dup_res.status_code == 400
    assert dup_res.json()["error"]["code"] == "DUPLICATE_INGREDIENT"

    # 3. Create Ingredient "Fresh Whole Milk"
    res2 = client.post(
        "/api/v1/inventory/ingredients",
        headers=headers_a,
        json={
            "name": "Fresh Whole Milk",
            "unit": "ML",
            "min_stock_threshold": 2000.0,
            "average_unit_cost": 25.0,
        },
    )
    assert res2.status_code == 201
    ing2_id = res2.json()["data"]["id"]

    # 4. List ingredients
    list_res = client.get("/api/v1/inventory/ingredients", headers=headers_a)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 2

    # 5. Get ingredient by ID
    get_res = client.get(f"/api/v1/inventory/ingredients/{ing1_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == ing1_id

    # 6. Verify inventory balances exist for both outlets of Tenant A
    with engine.connect() as conn:
        balances = conn.execute(
            text("SELECT outlet_id, on_hand_qty FROM inventory_balances WHERE ingredient_id = :ing_id"),
            {"ing_id": ing1_id},
        ).fetchall()
        # Should have initialized balance records for both outlet_a1 and outlet_a2
        assert len(balances) == 2
        for b in balances:
            assert b[1] == 0.0


def test_product_variants_and_addons_configuration(client, setup_tenants):
    """FR-017, FR-018, FR-019: Product, variant, and addon configuration."""
    headers_a = setup_tenants["headers_a"]

    # Fetch Category ID
    cats = client.get("/api/v1/catalog/categories", headers=headers_a).json()["data"]
    coffee_cat_id = cats[0]["id"]

    # 1. Create Product "Caramel Macchiato"
    product_payload = {
        "category_id": coffee_cat_id,
        "name": "Caramel Macchiato",
        "description": "Freshly brewed espresso with steamed vanilla milk and caramel drizzle",
        "base_price": 38000.0,
        "preparation_area": "BAR",
        "allow_outlet_availability_override": True,
        "variants": [
            {"name": "Regular", "price_delta": 0.0},
            {"name": "Large", "price_delta": 6000.0},
        ],
        "addons": [
            {"name": "Extra Espresso Shot", "price": 7000.0},
            {"name": "Caramel Drizzle", "price": 4000.0},
        ],
    }
    res = client.post("/api/v1/catalog/products", headers=headers_a, json=product_payload)
    assert res.status_code == 201
    prod = res.json()["data"]
    assert prod["name"] == "Caramel Macchiato"
    assert float(prod["base_price"]) == 38000.0
    assert len(prod["variants"]) == 2
    assert len(prod["addons"]) == 2
    prod_id = prod["id"]

    # 2. Add individual variant via endpoint
    var_res = client.post(
        f"/api/v1/catalog/products/{prod_id}/variants",
        headers=headers_a,
        json={"name": "Extra Large", "price_delta": 10000.0},
    )
    assert var_res.status_code == 201
    assert var_res.json()["data"]["name"] == "Extra Large"

    # 3. Add individual addon via endpoint
    addon_res = client.post(
        f"/api/v1/catalog/products/{prod_id}/addons",
        headers=headers_a,
        json={"name": "Oat Milk Sub", "price": 8000.0},
    )
    assert addon_res.status_code == 201
    assert addon_res.json()["data"]["name"] == "Oat Milk Sub"

    # 4. Fetch product and verify variants & addons
    prod_check = client.get(f"/api/v1/catalog/products/{prod_id}", headers=headers_a).json()["data"]
    assert len(prod_check["variants"]) == 3
    assert len(prod_check["addons"]) == 3


def test_recipe_composition_and_cost_calculation(client, setup_tenants):
    """BD-002, FR-086: Central recipe composition (BOM) and automated food cost calculation."""
    headers_a = setup_tenants["headers_a"]

    # Fetch product and ingredients
    prods = client.get("/api/v1/catalog/products", headers=headers_a).json()["data"]
    prod = [p for p in prods if p["name"] == "Caramel Macchiato"][0]
    prod_id = prod["id"]

    ings = client.get("/api/v1/inventory/ingredients", headers=headers_a).json()["data"]
    ing_beans = [i for i in ings if "Beans" in i["name"]][0]
    ing_milk = [i for i in ings if "Milk" in i["name"]][0]

    # Beans: 18g @ 150 = 2700.00
    # Milk: 180ml @ 25 = 4500.00
    # Expected total food cost = 7200.00
    recipe_payload = {
        "items": [
            {
                "ingredient_id": ing_beans["id"],
                "quantity_required": 18.0,
            },
            {
                "ingredient_id": ing_milk["id"],
                "quantity_required": 180.0,
            },
        ]
    }

    # 1. Configure Recipe
    set_res = client.put(
        f"/api/v1/catalog/products/{prod_id}/recipe",
        headers=headers_a,
        json=recipe_payload,
    )
    assert set_res.status_code == 200, set_res.text
    recipe = set_res.json()["data"]
    assert recipe["product_id"] == prod_id
    assert len(recipe["items"]) == 2
    assert float(recipe["total_recipe_cost"]) == 7200.00

    # 2. Retrieve Recipe endpoint
    get_res = client.get(f"/api/v1/catalog/products/{prod_id}/recipe", headers=headers_a)
    assert get_res.status_code == 200
    recipe_get = get_res.json()["data"]
    assert float(recipe_get["total_recipe_cost"]) == 7200.00

    # 3. Update ingredient average unit cost and verify cost recalculation
    # Update milk cost from 25 to 30: new total = 2700 + (180 * 30 = 5400) = 8100.00
    patch_ing = client.patch(
        f"/api/v1/inventory/ingredients/{ing_milk['id']}",
        headers=headers_a,
        json={"average_unit_cost": 30.0},
    )
    assert patch_ing.status_code == 200

    recalc_res = client.get(f"/api/v1/catalog/products/{prod_id}/recipe", headers=headers_a)
    assert recalc_res.status_code == 200
    assert float(recalc_res.json()["data"]["total_recipe_cost"]) == 8100.00


def test_outlet_product_availability_toggle(client, setup_tenants):
    """FR-021: Outlet-level availability toggle when central policy permits."""
    headers_a = setup_tenants["headers_a"]
    outlet_a1_id = setup_tenants["outlet_a1_id"]
    outlet_a2_id = setup_tenants["outlet_a2_id"]

    prods = client.get("/api/v1/catalog/products", headers=headers_a).json()["data"]
    prod_allowed = [p for p in prods if p["allow_outlet_availability_override"]][0]
    prod_id = prod_allowed["id"]

    # 1. Toggle availability to False at Outlet 1 (e.g. sold out locally)
    res = client.patch(
        f"/api/v1/outlets/{outlet_a1_id}/products/{prod_id}/availability",
        headers=headers_a,
        json={"is_available": False},
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_available"] is False

    # 2. Check Outlet 1 menu: item is marked unavailable
    menu_a1 = client.get(f"/api/v1/outlets/{outlet_a1_id}/products", headers=headers_a).json()["data"]
    item_a1 = [item for item in menu_a1 if item["id"] == prod_id][0]
    assert item_a1["is_available"] is False

    # 3. Check Outlet 2 menu: item remains available (independent outlet state)
    menu_a2 = client.get(f"/api/v1/outlets/{outlet_a2_id}/products", headers=headers_a).json()["data"]
    item_a2 = [item for item in menu_a2 if item["id"] == prod_id][0]
    assert item_a2["is_available"] is True

    # 4. Toggle back to True at Outlet 1
    res_back = client.patch(
        f"/api/v1/outlets/{outlet_a1_id}/products/{prod_id}/availability",
        headers=headers_a,
        json={"is_available": True},
    )
    assert res_back.status_code == 200
    assert res_back.json()["data"]["is_available"] is True

    # 5. Create a product with allow_outlet_availability_override = False
    cats = client.get("/api/v1/catalog/categories", headers=headers_a).json()["data"]
    cat_id = cats[0]["id"]

    locked_res = client.post(
        "/api/v1/catalog/products",
        headers=headers_a,
        json={
            "category_id": cat_id,
            "name": "Signature Espresso Locked",
            "base_price": 25000.0,
            "allow_outlet_availability_override": False,
        },
    )
    assert locked_res.status_code == 201
    locked_prod_id = locked_res.json()["data"]["id"]

    # 6. Attempting to toggle availability on locked product must fail
    fail_res = client.patch(
        f"/api/v1/outlets/{outlet_a1_id}/products/{locked_prod_id}/availability",
        headers=headers_a,
        json={"is_available": False},
    )
    assert fail_res.status_code == 400
    assert fail_res.json()["error"]["code"] == "OVERRIDE_NOT_ALLOWED"


def test_outlet_price_override_strictly_forbidden_br_005(client, setup_tenants):
    """BR-005, BD-001: Centralized pricing is strictly enforced; outlet price overrides are forbidden."""
    headers_a = setup_tenants["headers_a"]
    outlet_a1_id = setup_tenants["outlet_a1_id"]

    prods = client.get("/api/v1/catalog/products", headers=headers_a).json()["data"]
    prod_id = prods[0]["id"]

    # Attempt to post price override
    res = client.post(
        f"/api/v1/outlets/{outlet_a1_id}/products/{prod_id}/price-override",
        headers=headers_a,
        json={"override_price": 50000.0},
    )
    assert res.status_code == 403
    assert res.json()["status"] == "error"
    assert res.json()["error"]["code"] == "PRICE_OVERRIDE_NOT_ALLOWED"

    # Attempt to patch price override
    res_patch = client.patch(
        f"/api/v1/outlets/{outlet_a1_id}/products/{prod_id}/price-override",
        headers=headers_a,
        json={"override_price": 50000.0},
    )
    assert res_patch.status_code == 403
    assert res_patch.json()["error"]["code"] == "PRICE_OVERRIDE_NOT_ALLOWED"


def test_cross_tenant_catalog_isolation(client, setup_tenants):
    """BR-001, NFR-003: Strict multi-tenant isolation for categories, products, recipes, and ingredients."""
    headers_a = setup_tenants["headers_a"]
    headers_b = setup_tenants["headers_b"]
    outlet_b1_id = setup_tenants["outlet_b1_id"]

    # Fetch Tenant A artifacts
    cat_a = client.get("/api/v1/catalog/categories", headers=headers_a).json()["data"][0]
    prod_a = client.get("/api/v1/catalog/products", headers=headers_a).json()["data"][0]
    ing_a = client.get("/api/v1/inventory/ingredients", headers=headers_a).json()["data"][0]

    # 1. Tenant B cannot access Tenant A's category
    res_cat = client.get(f"/api/v1/catalog/categories/{cat_a['id']}", headers=headers_b)
    assert res_cat.status_code == 404
    assert res_cat.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

    # 2. Tenant B cannot access Tenant A's product
    res_prod = client.get(f"/api/v1/catalog/products/{prod_a['id']}", headers=headers_b)
    assert res_prod.status_code == 404
    assert res_prod.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    # 3. Tenant B cannot access Tenant A's ingredient
    res_ing = client.get(f"/api/v1/inventory/ingredients/{ing_a['id']}", headers=headers_b)
    assert res_ing.status_code == 404
    assert res_ing.json()["error"]["code"] == "INGREDIENT_NOT_FOUND"

    # 4. Tenant B catalog listing is empty initially
    b_prods = client.get("/api/v1/catalog/products", headers=headers_b).json()["data"]
    assert len(b_prods) == 0

    # 5. Create category and product in Tenant B
    cat_b = client.post(
        "/api/v1/catalog/categories",
        headers=headers_b,
        json={"name": "Burgers & Sides"},
    ).json()["data"]

    prod_b = client.post(
        "/api/v1/catalog/products",
        headers=headers_b,
        json={
            "category_id": cat_b["id"],
            "name": "Classic Cheeseburger",
            "base_price": 55000.0,
        },
    ).json()["data"]

    # 6. Tenant B cannot use Tenant A's ingredient in its recipe
    fail_recipe = client.put(
        f"/api/v1/catalog/products/{prod_b['id']}/recipe",
        headers=headers_b,
        json={"items": [{"ingredient_id": ing_a["id"], "quantity_required": 1.0}]},
    )
    assert fail_recipe.status_code == 404
    assert fail_recipe.json()["error"]["code"] == "INGREDIENT_NOT_FOUND"

    # 7. Tenant B cannot toggle Tenant A's product availability
    fail_avail = client.patch(
        f"/api/v1/outlets/{outlet_b1_id}/products/{prod_a['id']}/availability",
        headers=headers_b,
        json={"is_available": False},
    )
    assert fail_avail.status_code == 404
    assert fail_avail.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_role_based_access_rejections(client, setup_tenants):
    """BD-001, BR-004: Non-Central Admin staff (e.g. Waiter) cannot manage catalog or recipes."""
    waiter_headers = setup_tenants["waiter_headers"]
    headers_a = setup_tenants["headers_a"]

    cat_a = client.get("/api/v1/catalog/categories", headers=headers_a).json()["data"][0]
    prod_a = client.get("/api/v1/catalog/products", headers=headers_a).json()["data"][0]

    # 1. Waiter cannot create category
    res1 = client.post(
        "/api/v1/catalog/categories",
        headers=waiter_headers,
        json={"name": "Unauthorized Category"},
    )
    assert res1.status_code == 403
    assert res1.json()["error"]["code"] == "FORBIDDEN"

    # 2. Waiter cannot create product
    res2 = client.post(
        "/api/v1/catalog/products",
        headers=waiter_headers,
        json={
            "category_id": cat_a["id"],
            "name": "Unauthorized Product",
            "base_price": 10000.0,
        },
    )
    assert res2.status_code == 403
    assert res2.json()["error"]["code"] == "FORBIDDEN"

    # 3. Waiter cannot create ingredient
    res3 = client.post(
        "/api/v1/inventory/ingredients",
        headers=waiter_headers,
        json={"name": "Unauthorized Ingredient", "unit": "KG"},
    )
    assert res3.status_code == 403
    assert res3.json()["error"]["code"] == "FORBIDDEN"

    # 4. Waiter cannot configure recipe
    res4 = client.put(
        f"/api/v1/catalog/products/{prod_a['id']}/recipe",
        headers=waiter_headers,
        json={"items": []},
    )
    assert res4.status_code == 403
    assert res4.json()["error"]["code"] == "FORBIDDEN"
