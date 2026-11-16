import uuid
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class TenantBase(BaseModel):
    name: str = Field(..., max_length=150)


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    service_charge_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    allow_negative_inventory: Optional[bool] = None
    reason: Optional[str] = Field(None, description="Reason for sensitive policy update")


class TenantOut(TenantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tax_rate: Decimal
    service_charge_rate: Decimal
    allow_negative_inventory: bool
    created_at: datetime
    updated_at: datetime


class OutletBase(BaseModel):
    name: str = Field(..., max_length=150)
    address: Optional[str] = None
    payment_timing: Literal["PAY_BEFORE_SERVING", "PAY_AFTER_SERVING"] = "PAY_AFTER_SERVING"


class OutletCreate(OutletBase):
    pass


class OutletUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    address: Optional[str] = None
    payment_timing: Optional[Literal["PAY_BEFORE_SERVING", "PAY_AFTER_SERVING"]] = None
    is_active: Optional[bool] = None


class OutletOut(OutletBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
