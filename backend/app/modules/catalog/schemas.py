import uuid
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime


# ============================================================================
# VARIANT & ADDON SCHEMAS
# ============================================================================

class VariantCreate(BaseModel):
    name: str = Field(..., max_length=100)
    price_delta: Decimal = Field(default=Decimal("0.00"))


class VariantUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    price_delta: Optional[Decimal] = None
    is_active: Optional[bool] = None


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    name: str
    price_delta: Decimal
    is_active: bool


class AddonCreate(BaseModel):
    name: str = Field(..., max_length=100)
    price: Decimal = Field(default=Decimal("0.00"), ge=0)


class AddonUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class AddonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    name: str
    price: Decimal
    is_active: bool


# ============================================================================
# RECIPE SCHEMAS
# ============================================================================

class RecipeItemCreate(BaseModel):
    ingredient_id: uuid.UUID
    quantity_required: Decimal = Field(..., gt=0)
    variant_id: Optional[uuid.UUID] = None


class RecipeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ingredient_id: uuid.UUID
    ingredient_name: Optional[str] = None
    unit: Optional[str] = None
    quantity_required: Decimal
    average_unit_cost: Optional[Decimal] = None
    item_cost: Optional[Decimal] = None
    variant_id: Optional[uuid.UUID] = None
    variant_name: Optional[str] = None


class RecipeSetRequest(BaseModel):
    items: List[RecipeItemCreate]


class RecipeOut(BaseModel):
    product_id: uuid.UUID
    product_name: str
    base_price: Decimal
    total_recipe_cost: Decimal
    items: List[RecipeItemOut]


# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    base_price: Decimal = Field(..., ge=0)
    allow_outlet_availability_override: bool = True


class ProductCreate(ProductBase):
    category_id: uuid.UUID
    variants: Optional[List[VariantCreate]] = None
    addons: Optional[List[AddonCreate]] = None
    recipe_items: Optional[List[RecipeItemCreate]] = None


class ProductUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    allow_outlet_availability_override: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    category_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    variants: List[VariantOut] = []
    addons: List[AddonOut] = []
    recipe_items: List[RecipeItemOut] = []
    recipe_cost: Optional[Decimal] = None


# ============================================================================
# OUTLET AVAILABILITY & PRICE OVERRIDE ATTEMPTS
# ============================================================================

class OutletAvailabilityUpdate(BaseModel):
    is_available: bool


class OutletAvailabilityOut(BaseModel):
    outlet_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    base_price: Decimal
    is_available: bool
    allow_outlet_availability_override: bool
    updated_at: datetime


class PriceOverrideRequest(BaseModel):
    price: Optional[Decimal] = None
    override_price: Optional[Decimal] = None
