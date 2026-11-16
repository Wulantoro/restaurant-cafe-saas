import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import status

from app.core.exceptions import DomainException
from app.modules.tenancy.models import Tenant, Outlet
from app.modules.tenancy.schemas import TenantUpdate, OutletCreate, OutletUpdate
from app.modules.iam.models import User
from app.modules.audit.service import record_audit_log


def get_tenant_by_id(db: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise DomainException(
            code="TENANT_NOT_FOUND",
            message="Business tenant not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return tenant


def update_tenant_settings(
    db: Session,
    tenant_id: uuid.UUID,
    data: TenantUpdate,
    current_user: User,
) -> Tenant:
    tenant = get_tenant_by_id(db, tenant_id)

    # 1. Negative inventory policy is restricted to Business Owner (BR-016, BD-007)
    if data.allow_negative_inventory is not None and data.allow_negative_inventory != tenant.allow_negative_inventory:
        if not current_user.is_owner:
            raise DomainException(
                code="FORBIDDEN",
                message="Only the Business Owner can modify the negative inventory policy",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        old_val = tenant.allow_negative_inventory
        new_val = data.allow_negative_inventory
        tenant.allow_negative_inventory = new_val

        # Mandatory audit log for negative inventory policy change
        record_audit_log(
            db=db,
            tenant_id=tenant.id,
            actor_id=current_user.id,
            action="UPDATE_NEGATIVE_INVENTORY_POLICY",
            entity_type="TENANT",
            entity_id=tenant.id,
            old_values={"allow_negative_inventory": old_val},
            new_values={"allow_negative_inventory": new_val},
            reason=data.reason or "Owner updated negative inventory policy",
        )

    # 2. Centralized tax & service charge updates (Central Admin or Owner, BD-001)
    if data.tax_rate is not None or data.service_charge_rate is not None or data.name is not None:
        if not (current_user.is_owner or current_user.is_central_admin):
            raise DomainException(
                code="FORBIDDEN",
                message="Central Admin or Owner authority required to update central business settings",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if data.name is not None:
            tenant.name = data.name
        if data.tax_rate is not None:
            tenant.tax_rate = data.tax_rate
        if data.service_charge_rate is not None:
            tenant.service_charge_rate = data.service_charge_rate

    db.commit()
    db.refresh(tenant)
    return tenant


def create_outlet(
    db: Session,
    tenant_id: uuid.UUID,
    data: OutletCreate,
    current_user: User,
) -> Outlet:
    # Requires Owner or Central Admin (FR-005)
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Only Owner or Central Admin can create outlets",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    outlet = Outlet(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=data.name,
        address=data.address,
        payment_timing=data.payment_timing,
        is_active=True,
    )
    db.add(outlet)
    db.commit()
    db.refresh(outlet)
    return outlet


def get_outlet_by_id(
    db: Session,
    tenant_id: uuid.UUID,
    outlet_id: uuid.UUID,
) -> Outlet:
    outlet = (
        db.query(Outlet)
        .filter(Outlet.id == outlet_id, Outlet.tenant_id == tenant_id)
        .first()
    )
    if not outlet:
        raise DomainException(
            code="OUTLET_NOT_FOUND",
            message="Outlet not found or does not belong to your business",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return outlet


def list_outlets(
    db: Session,
    tenant_id: uuid.UUID,
    is_active: Optional[bool] = None,
) -> List[Outlet]:
    query = db.query(Outlet).filter(Outlet.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(Outlet.is_active == is_active)
    return query.order_by(Outlet.created_at.asc()).all()


def update_outlet(
    db: Session,
    tenant_id: uuid.UUID,
    outlet_id: uuid.UUID,
    data: OutletUpdate,
    current_user: User,
) -> Outlet:
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Only Owner or Central Admin can update outlet configuration",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    outlet = get_outlet_by_id(db, tenant_id, outlet_id)

    if data.name is not None:
        outlet.name = data.name
    if data.address is not None:
        outlet.address = data.address
    if data.payment_timing is not None:
        outlet.payment_timing = data.payment_timing
    if data.is_active is not None:
        outlet.is_active = data.is_active

    db.commit()
    db.refresh(outlet)
    return outlet
