import uuid
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterBusinessRequest(BaseModel):
    business_name: str = Field(..., max_length=150)
    owner_full_name: str = Field(..., max_length=150)
    owner_email: EmailStr = Field(...)
    owner_password: str = Field(..., min_length=8)
    initial_outlet_name: str = Field(..., max_length=150)
    initial_outlet_address: Optional[str] = None
    initial_outlet_payment_timing: Literal["PAY_BEFORE_SERVING", "PAY_AFTER_SERVING"] = "PAY_AFTER_SERVING"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: Optional[uuid.UUID] = None


class UserOutletRoleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    outlet_id: uuid.UUID
    role: str
    created_at: datetime


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    full_name: str
    email: str
    is_central_admin: bool
    is_owner: bool
    is_active: bool
    created_at: datetime
    roles: List[UserOutletRoleSummary] = []


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(BaseModel):
    full_name: str = Field(..., max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    is_central_admin: bool = False
    initial_outlet_id: Optional[uuid.UUID] = None
    initial_role: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    password: Optional[str] = Field(None, min_length=8)
    is_central_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    reason: Optional[str] = None


class RoleAssignRequest(BaseModel):
    outlet_id: uuid.UUID
    role: str = Field(..., description="MANAGER, CASHIER, WAITER, KITCHEN, INVENTORY, PURCHASING")


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    outlet_id: uuid.UUID
    role: str
    created_at: datetime


class MeOutletInfo(BaseModel):
    outlet_id: uuid.UUID
    outlet_name: str
    payment_timing: str
    roles: List[str]


class MeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    tenant_name: str
    full_name: str
    email: str
    is_central_admin: bool
    is_owner: bool
    is_active: bool
    outlets: List[MeOutletInfo]
