import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Numeric,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="menu_categories_tenant_id_id_key"),
    )

    tenant = relationship("Tenant")
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    category_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(Numeric(12, 2), nullable=False)
    allow_outlet_availability_override = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "category_id"],
            ["menu_categories.tenant_id", "menu_categories.id"],
            name="products_tenant_id_category_id_fkey",
        ),
        UniqueConstraint("tenant_id", "id", name="products_tenant_id_id_key"),
    )

    tenant = relationship("Tenant")
    category = relationship("MenuCategory", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    addons = relationship("ProductAddon", back_populates="product", cascade="all, delete-orphan")
    recipe_items = relationship("RecipeItem", back_populates="product", cascade="all, delete-orphan")
    outlet_availabilities = relationship("OutletProductAvailability", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(100), nullable=False)
    price_delta = Column(Numeric(12, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            ondelete="CASCADE",
            name="product_variants_tenant_id_product_id_fkey",
        ),
        UniqueConstraint("tenant_id", "id", name="product_variants_tenant_id_id_key"),
    )

    product = relationship("Product", back_populates="variants")
    recipe_items = relationship("RecipeItem", back_populates="variant", cascade="all, delete-orphan")


class ProductAddon(Base):
    __tablename__ = "product_addons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            ondelete="CASCADE",
            name="product_addons_tenant_id_product_id_fkey",
        ),
        UniqueConstraint("tenant_id", "id", name="product_addons_tenant_id_id_key"),
    )

    product = relationship("Product", back_populates="addons")


class OutletProductAvailability(Base):
    __tablename__ = "outlet_product_availability"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    outlet_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    is_available = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "outlet_id", "product_id", name="outlet_product_availability_pkey"),
        ForeignKeyConstraint(
            ["tenant_id", "outlet_id"],
            ["outlets.tenant_id", "outlets.id"],
            ondelete="CASCADE",
            name="outlet_product_availability_tenant_id_outlet_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            ondelete="CASCADE",
            name="outlet_product_availability_tenant_id_product_id_fkey",
        ),
    )

    outlet = relationship("Outlet")
    product = relationship("Product", back_populates="outlet_availabilities")


# Alias for explicit reference
OutletPriceOverride = OutletProductAvailability

