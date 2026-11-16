from sqlalchemy import text
from app.core.database import engine


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_readiness_and_schema_tables(client):
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["database"] == "connected"

    expected_tables = {
        "tenants", "outlets", "users", "user_outlet_roles",
        "menu_categories", "products", "product_variants", "product_addons",
        "outlet_product_availability", "ingredients", "recipe_items",
        "inventory_balances", "inventory_movements", "suppliers",
        "purchase_orders", "purchase_order_items", "goods_receipts",
        "goods_receipt_items", "dining_tables", "orders",
        "kitchen_submissions", "order_items", "inventory_reservations",
        "order_modification_requests", "cashier_shifts", "payments",
        "payment_item_allocations", "refund_requests", "audit_logs"
    }

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        existing_tables = {row[0] for row in result}

    assert expected_tables.issubset(existing_tables)
