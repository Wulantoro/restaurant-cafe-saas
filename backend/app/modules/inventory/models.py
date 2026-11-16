import uuid
from sqlalchemy import (
    Column,
    String,
    Numeric,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(150), nullable=False)
    unit = Column(String(30), nullable=False)
    min_stock_threshold = Column(Numeric(12, 3), nullable=False, default=0.000)
    average_unit_cost = Column(Numeric(12, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ingredients_tenant_id_id_key"),
    )

    tenant = relationship("Tenant")
    recipe_items = relationship("RecipeItem", back_populates="ingredient", cascade="all, delete-orphan")
    balances = relationship("InventoryBalance", back_populates="ingredient", cascade="all, delete-orphan")


class RecipeItem(Base):
    __tablename__ = "recipe_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    variant_id = Column(UUID(as_uuid=True), nullable=True)
    ingredient_id = Column(UUID(as_uuid=True), nullable=False)
    quantity_required = Column(Numeric(12, 3), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            ondelete="CASCADE",
            name="recipe_items_tenant_id_product_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "variant_id"],
            ["product_variants.tenant_id", "product_variants.id"],
            ondelete="CASCADE",
            name="recipe_items_tenant_id_variant_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "ingredient_id"],
            ["ingredients.tenant_id", "ingredients.id"],
            ondelete="RESTRICT",
            name="recipe_items_tenant_id_ingredient_id_fkey",
        ),
    )

    product = relationship("Product", back_populates="recipe_items")
    variant = relationship("ProductVariant", back_populates="recipe_items")
    ingredient = relationship("Ingredient", back_populates="recipe_items")


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    outlet_id = Column(UUID(as_uuid=True), nullable=False)
    ingredient_id = Column(UUID(as_uuid=True), nullable=False)
    on_hand_qty = Column(Numeric(12, 3), nullable=False, default=0.000)
    reserved_qty = Column(Numeric(12, 3), nullable=False, default=0.000)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "outlet_id"],
            ["outlets.tenant_id", "outlets.id"],
            ondelete="RESTRICT",
            name="inventory_balances_tenant_id_outlet_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "ingredient_id"],
            ["ingredients.tenant_id", "ingredients.id"],
            ondelete="RESTRICT",
            name="inventory_balances_tenant_id_ingredient_id_fkey",
        ),
        UniqueConstraint("tenant_id", "outlet_id", "ingredient_id", name="inventory_balances_tenant_id_outlet_id_ingredient_id_key"),
    )

    outlet = relationship("Outlet")
    ingredient = relationship("Ingredient", back_populates="balances")

