import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant_context, require_owner, require_central_admin_or_owner
from app.modules.iam.models import User
from app.modules.tenancy.models import Tenant
from app.modules.tenancy.schemas import TenantOut, TenantUpdate, OutletOut, OutletCreate, OutletUpdate
from app.modules.tenancy import service

router = APIRouter(tags=["Tenancy & Outlets"])


@router.get("/tenants/me", response_model=dict, status_code=status.HTTP_200_OK)
def get_current_tenant(
    tenant: Tenant = Depends(get_current_tenant_context),
):
    """Retrieve the business profile and settings for the authenticated tenant."""
    return {
        "status": "success",
        "data": TenantOut.model_validate(tenant).model_dump(mode="json"),
    }


@router.patch("/tenants/me", response_model=dict, status_code=status.HTTP_200_OK)
@router.patch("/tenant/settings", response_model=dict, status_code=status.HTTP_200_OK)
def update_tenant_settings(
    payload: TenantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update tenant centralized settings: tax_rate, service_charge_rate, allow_negative_inventory."""
    tenant = service.update_tenant_settings(
        db=db,
        tenant_id=current_user.tenant_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": TenantOut.model_validate(tenant).model_dump(mode="json"),
    }


@router.post("/outlets", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_outlet(
    payload: OutletCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new outlet under the current tenant (Central Admin / Owner)."""
    outlet = service.create_outlet(
        db=db,
        tenant_id=current_user.tenant_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": OutletOut.model_validate(outlet).model_dump(mode="json"),
    }


@router.get("/outlets", response_model=dict, status_code=status.HTTP_200_OK)
def list_outlets(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all outlets belonging to the authenticated tenant."""
    outlets = service.list_outlets(
        db=db,
        tenant_id=current_user.tenant_id,
        is_active=is_active,
    )
    return {
        "status": "success",
        "data": [OutletOut.model_validate(o).model_dump(mode="json") for o in outlets],
    }


@router.get("/outlets/{outlet_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_outlet(
    outlet_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific outlet within the current tenant."""
    outlet = service.get_outlet_by_id(
        db=db,
        tenant_id=current_user.tenant_id,
        outlet_id=outlet_id,
    )
    return {
        "status": "success",
        "data": OutletOut.model_validate(outlet).model_dump(mode="json"),
    }


@router.patch("/outlets/{outlet_id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_outlet(
    outlet_id: uuid.UUID,
    payload: OutletUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update outlet details or payment_timing policy."""
    outlet = service.update_outlet(
        db=db,
        tenant_id=current_user.tenant_id,
        outlet_id=outlet_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": OutletOut.model_validate(outlet).model_dump(mode="json"),
    }
