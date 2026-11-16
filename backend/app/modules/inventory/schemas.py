import uuid
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class IngredientBase(BaseModel):
    name: str = Field(..., max_length=150)
    unit: str = Field(..., max_length=30)
    min_stock_threshold: Decimal = Field(default=Decimal("0.000"), ge=0)
    average_unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0)


class IngredientCreate(IngredientBase):
    pass


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    unit: Optional[str] = Field(None, max_length=30)
    min_stock_threshold: Optional[Decimal] = Field(None, ge=0)
    average_unit_cost: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class IngredientOut(IngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
