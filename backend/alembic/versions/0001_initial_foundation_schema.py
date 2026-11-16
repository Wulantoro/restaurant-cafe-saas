"""Initial foundation schema aligned with SAD-FOUNDATION-001

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-14 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    CREATE TYPE payment_timing_enum AS ENUM ('PAY_BEFORE_SERVING', 'PAY_AFTER_SERVING');
    CREATE TYPE order_type_enum AS ENUM ('DINE_IN', 'TAKEAWAY');
    CREATE TYPE order_status_enum AS ENUM ('OPEN', 'CLOSED', 'CANCELLED');
    CREATE TYPE payment_status_enum AS ENUM ('UNPAID', 'PARTIALLY_PAID', 'PAID', 'REFUNDED');
    CREATE TYPE kitchen_status_enum AS ENUM ('PENDING', 'PREPARING', 'READY', 'SERVED', 'CANCELLED');
    CREATE TYPE approval_status_enum AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
    CREATE TYPE po_status_enum AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PARTIALLY_RECEIVED', 'COMPLETED', 'CANCELLED');
    CREATE TYPE movement_type_enum AS ENUM ('RECEIVING', 'CONSUMPTION', 'WASTE', 'ADJUSTMENT', 'OPNAME');
    CREATE TYPE split_bill_type_enum AS ENUM ('NONE', 'SPLIT_BY_ITEMS', 'SPLIT_EQUALLY');

    CREATE TABLE tenants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(150) NOT NULL,
        tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0.00,
        service_charge_rate NUMERIC(5,2) NOT NULL DEFAULT 0.00,
        allow_negative_inventory BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE outlets (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        name VARCHAR(150) NOT NULL,
        address TEXT,
        payment_timing payment_timing_enum NOT NULL DEFAULT 'PAY_AFTER_SERVING',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        full_name VARCHAR(150) NOT NULL,
        email VARCHAR(150) NOT NULL,
        password_hash TEXT NOT NULL,
        is_central_admin BOOLEAN NOT NULL DEFAULT FALSE,
        is_owner BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (tenant_id, email),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE user_outlet_roles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        user_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        role VARCHAR(50) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id) ON DELETE CASCADE,
        UNIQUE (tenant_id, user_id, outlet_id, role)
    );

    CREATE TABLE menu_categories (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        name VARCHAR(100) NOT NULL,
        sort_order INT NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        category_id UUID NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        base_price NUMERIC(12,2) NOT NULL CHECK (base_price >= 0),
        allow_outlet_availability_override BOOLEAN NOT NULL DEFAULT TRUE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, category_id) REFERENCES menu_categories(tenant_id, id),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE product_variants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        product_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL,
        price_delta NUMERIC(12,2) NOT NULL DEFAULT 0.00,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE product_addons (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        product_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL,
        price NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (price >= 0),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE outlet_product_availability (
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        product_id UUID NOT NULL,
        is_available BOOLEAN NOT NULL DEFAULT TRUE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (tenant_id, outlet_id, product_id),
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE
    );

    CREATE TABLE ingredients (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        name VARCHAR(150) NOT NULL,
        unit VARCHAR(30) NOT NULL,
        min_stock_threshold NUMERIC(12,3) NOT NULL DEFAULT 0,
        average_unit_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE recipe_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        product_id UUID NOT NULL,
        variant_id UUID NULL,
        ingredient_id UUID NOT NULL,
        quantity_required NUMERIC(12,3) NOT NULL CHECK (quantity_required > 0),
        FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, variant_id) REFERENCES product_variants(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id) ON DELETE RESTRICT
    );

    CREATE TABLE inventory_balances (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        ingredient_id UUID NOT NULL,
        on_hand_qty NUMERIC(12,3) NOT NULL DEFAULT 0,
        reserved_qty NUMERIC(12,3) NOT NULL DEFAULT 0,
        version INT NOT NULL DEFAULT 1,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id) ON DELETE RESTRICT,
        FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id) ON DELETE RESTRICT,
        UNIQUE (tenant_id, outlet_id, ingredient_id)
    );

    CREATE TABLE inventory_movements (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        ingredient_id UUID NOT NULL,
        movement_type movement_type_enum NOT NULL,
        quantity_delta NUMERIC(12,3) NOT NULL,
        unit_cost NUMERIC(12,2),
        reference_type VARCHAR(50),
        reference_id UUID,
        reason TEXT,
        is_negative_stock_exception BOOLEAN NOT NULL DEFAULT FALSE,
        created_by UUID NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id),
        FOREIGN KEY (tenant_id, created_by) REFERENCES users(tenant_id, id)
    );

    CREATE TABLE suppliers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
        name VARCHAR(150) NOT NULL,
        contact_info TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE purchase_orders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        supplier_id UUID NOT NULL,
        po_number VARCHAR(50) NOT NULL,
        status po_status_enum NOT NULL DEFAULT 'DRAFT',
        requested_by UUID NOT NULL,
        approved_by UUID NULL,
        approved_at TIMESTAMPTZ NULL,
        rejection_reason TEXT NULL,
        version INT NOT NULL DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, supplier_id) REFERENCES suppliers(tenant_id, id),
        FOREIGN KEY (tenant_id, requested_by) REFERENCES users(tenant_id, id),
        FOREIGN KEY (tenant_id, approved_by) REFERENCES users(tenant_id, id),
        UNIQUE (tenant_id, po_number),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE purchase_order_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        purchase_order_id UUID NOT NULL,
        ingredient_id UUID NOT NULL,
        ordered_qty NUMERIC(12,3) NOT NULL CHECK (ordered_qty > 0),
        received_qty NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (received_qty >= 0),
        unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
        FOREIGN KEY (tenant_id, purchase_order_id) REFERENCES purchase_orders(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE goods_receipts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        purchase_order_id UUID NOT NULL,
        received_by UUID NOT NULL,
        notes TEXT,
        received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, purchase_order_id) REFERENCES purchase_orders(tenant_id, id),
        FOREIGN KEY (tenant_id, received_by) REFERENCES users(tenant_id, id),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE goods_receipt_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        goods_receipt_id UUID NOT NULL,
        po_item_id UUID NOT NULL,
        accepted_qty NUMERIC(12,3) NOT NULL CHECK (accepted_qty >= 0),
        rejected_qty NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (rejected_qty >= 0),
        FOREIGN KEY (tenant_id, goods_receipt_id) REFERENCES goods_receipts(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, po_item_id) REFERENCES purchase_order_items(tenant_id, id)
    );

    CREATE TABLE dining_tables (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        table_number VARCHAR(30) NOT NULL,
        capacity INT NOT NULL DEFAULT 2,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        UNIQUE (tenant_id, outlet_id, table_number),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE orders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        table_id UUID NULL,
        order_number VARCHAR(50) NOT NULL,
        order_type order_type_enum NOT NULL,
        status order_status_enum NOT NULL DEFAULT 'OPEN',
        payment_status payment_status_enum NOT NULL DEFAULT 'UNPAID',
        tax_rate_snapshot NUMERIC(5,2) NOT NULL,
        service_charge_rate_snapshot NUMERIC(5,2) NOT NULL,
        subtotal_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
        discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
        tax_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
        service_charge_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
        grand_total_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
        paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
        created_by UUID NOT NULL,
        version INT NOT NULL DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        closed_at TIMESTAMPTZ NULL,
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, table_id) REFERENCES dining_tables(tenant_id, id),
        FOREIGN KEY (tenant_id, created_by) REFERENCES users(tenant_id, id),
        UNIQUE (tenant_id, order_number),
        UNIQUE (tenant_id, id)
    );

    CREATE UNIQUE INDEX uq_single_active_order_per_table 
    ON orders (tenant_id, outlet_id, table_id) 
    WHERE order_type = 'DINE_IN' AND status = 'OPEN';

    CREATE TABLE kitchen_submissions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        order_id UUID NOT NULL,
        batch_number INT NOT NULL,
        submitted_by UUID NOT NULL,
        submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, submitted_by) REFERENCES users(tenant_id, id),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE order_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        order_id UUID NOT NULL,
        kitchen_submission_id UUID NULL,
        product_id UUID NOT NULL,
        variant_id UUID NULL,
        product_name_snapshot VARCHAR(150) NOT NULL,
        variant_name_snapshot VARCHAR(100) NULL,
        unit_price_snapshot NUMERIC(12,2) NOT NULL,
        addons_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
        quantity INT NOT NULL CHECK (quantity > 0),
        line_total NUMERIC(12,2) NOT NULL,
        special_instructions TEXT,
        kitchen_status kitchen_status_enum NOT NULL DEFAULT 'PENDING',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, kitchen_submission_id) REFERENCES kitchen_submissions(tenant_id, id),
        FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE inventory_reservations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        order_item_id UUID NOT NULL,
        ingredient_id UUID NOT NULL,
        reserved_qty NUMERIC(12,3) NOT NULL CHECK (reserved_qty > 0),
        status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
        is_negative_exception BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        resolved_at TIMESTAMPTZ NULL,
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, order_item_id) REFERENCES order_items(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id)
    );

    CREATE TABLE order_modification_requests (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        order_id UUID NOT NULL,
        reason TEXT NOT NULL,
        status approval_status_enum NOT NULL DEFAULT 'PENDING',
        requested_by UUID NOT NULL,
        reviewed_by UUID NULL,
        rejection_reason TEXT NULL,
        items_payload JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        reviewed_at TIMESTAMPTZ NULL,
        FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id),
        FOREIGN KEY (tenant_id, requested_by) REFERENCES users(tenant_id, id),
        FOREIGN KEY (tenant_id, reviewed_by) REFERENCES users(tenant_id, id)
    );

    CREATE TABLE cashier_shifts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        cashier_id UUID NOT NULL,
        opening_cash NUMERIC(12,2) NOT NULL DEFAULT 0,
        expected_cash NUMERIC(12,2) NULL,
        actual_cash NUMERIC(12,2) NULL,
        cash_discrepancy NUMERIC(12,2) NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
        opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        closed_at TIMESTAMPTZ NULL,
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, cashier_id) REFERENCES users(tenant_id, id),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE payments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        order_id UUID NOT NULL,
        shift_id UUID NOT NULL,
        idempotency_key VARCHAR(100) NOT NULL,
        payment_method VARCHAR(50) NOT NULL,
        split_type split_bill_type_enum NOT NULL DEFAULT 'NONE',
        amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
        processed_by UUID NOT NULL,
        paid_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id),
        FOREIGN KEY (tenant_id, shift_id) REFERENCES cashier_shifts(tenant_id, id),
        FOREIGN KEY (tenant_id, processed_by) REFERENCES users(tenant_id, id),
        UNIQUE (tenant_id, idempotency_key),
        UNIQUE (tenant_id, id)
    );

    CREATE TABLE payment_item_allocations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        payment_id UUID NOT NULL,
        order_item_id UUID NOT NULL,
        allocated_qty INT NOT NULL CHECK (allocated_qty > 0),
        allocated_amount NUMERIC(12,2) NOT NULL,
        FOREIGN KEY (tenant_id, payment_id) REFERENCES payments(tenant_id, id) ON DELETE CASCADE,
        FOREIGN KEY (tenant_id, order_item_id) REFERENCES order_items(tenant_id, id)
    );

    CREATE TABLE refund_requests (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        outlet_id UUID NOT NULL,
        order_id UUID NOT NULL,
        payment_id UUID NOT NULL,
        refund_amount NUMERIC(12,2) NOT NULL CHECK (refund_amount > 0),
        reason TEXT NOT NULL,
        status approval_status_enum NOT NULL DEFAULT 'PENDING',
        requested_by UUID NOT NULL,
        reviewed_by UUID NULL,
        rejection_reason TEXT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        reviewed_at TIMESTAMPTZ NULL,
        FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
        FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id),
        FOREIGN KEY (tenant_id, payment_id) REFERENCES payments(tenant_id, id),
        FOREIGN KEY (tenant_id, requested_by) REFERENCES users(tenant_id, id),
        FOREIGN KEY (tenant_id, reviewed_by) REFERENCES users(tenant_id, id)
    );

    CREATE TABLE audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL REFERENCES tenants(id),
        outlet_id UUID NULL,
        actor_id UUID NOT NULL,
        action VARCHAR(100) NOT NULL,
        entity_type VARCHAR(50) NOT NULL,
        entity_id UUID NOT NULL,
        old_values JSONB NULL,
        new_values JSONB NULL,
        reason TEXT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX idx_orders_tenant_outlet_status ON orders(tenant_id, outlet_id, status);
    CREATE INDEX idx_order_items_kitchen ON order_items(tenant_id, kitchen_status);
    CREATE INDEX idx_inventory_movements_lookup ON inventory_movements(tenant_id, outlet_id, ingredient_id, created_at DESC);
    CREATE INDEX idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS audit_logs CASCADE;
    DROP TABLE IF EXISTS refund_requests CASCADE;
    DROP TABLE IF EXISTS payment_item_allocations CASCADE;
    DROP TABLE IF EXISTS payments CASCADE;
    DROP TABLE IF EXISTS cashier_shifts CASCADE;
    DROP TABLE IF EXISTS order_modification_requests CASCADE;
    DROP TABLE IF EXISTS inventory_reservations CASCADE;
    DROP TABLE IF EXISTS order_items CASCADE;
    DROP TABLE IF EXISTS kitchen_submissions CASCADE;
    DROP TABLE IF EXISTS orders CASCADE;
    DROP TABLE IF EXISTS dining_tables CASCADE;
    DROP TABLE IF EXISTS goods_receipt_items CASCADE;
    DROP TABLE IF EXISTS goods_receipts CASCADE;
    DROP TABLE IF EXISTS purchase_order_items CASCADE;
    DROP TABLE IF EXISTS purchase_orders CASCADE;
    DROP TABLE IF EXISTS suppliers CASCADE;
    DROP TABLE IF EXISTS inventory_movements CASCADE;
    DROP TABLE IF EXISTS inventory_balances CASCADE;
    DROP TABLE IF EXISTS recipe_items CASCADE;
    DROP TABLE IF EXISTS ingredients CASCADE;
    DROP TABLE IF EXISTS outlet_product_availability CASCADE;
    DROP TABLE IF EXISTS product_addons CASCADE;
    DROP TABLE IF EXISTS product_variants CASCADE;
    DROP TABLE IF EXISTS products CASCADE;
    DROP TABLE IF EXISTS menu_categories CASCADE;
    DROP TABLE IF EXISTS user_outlet_roles CASCADE;
    DROP TABLE IF EXISTS users CASCADE;
    DROP TABLE IF EXISTS outlets CASCADE;
    DROP TABLE IF EXISTS tenants CASCADE;

    DROP TYPE IF EXISTS split_bill_type_enum;
    DROP TYPE IF EXISTS movement_type_enum;
    DROP TYPE IF EXISTS po_status_enum;
    DROP TYPE IF EXISTS approval_status_enum;
    DROP TYPE IF EXISTS kitchen_status_enum;
    DROP TYPE IF EXISTS payment_status_enum;
    DROP TYPE IF EXISTS order_status_enum;
    DROP TYPE IF EXISTS order_type_enum;
    DROP TYPE IF EXISTS payment_timing_enum;
    """)
