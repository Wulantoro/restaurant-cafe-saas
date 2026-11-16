import uuid
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import status

from app.core.exceptions import DomainException
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.modules.tenancy.models import Tenant, Outlet
from app.modules.iam.models import User, UserOutletRole
from app.modules.iam.schemas import (
    RegisterBusinessRequest,
    LoginRequest,
    UserCreate,
    UserUpdate,
    RoleAssignRequest,
    MeResponse,
    MeOutletInfo,
)
from app.modules.audit.service import record_audit_log

VALID_ROLES = {"MANAGER", "CASHIER", "WAITER", "KITCHEN", "INVENTORY", "PURCHASING"}


def register_business(db: Session, data: RegisterBusinessRequest) -> Tuple[str, str, User]:
    """FR-001, FR-002: Register a new business, creating tenant, initial outlet, and owner user."""
    # 1. Create Tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        name=data.business_name,
        tax_rate=0.00,
        service_charge_rate=0.00,
        allow_negative_inventory=False,
    )
    db.add(tenant)

    # 2. Create Initial Outlet
    outlet = Outlet(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name=data.initial_outlet_name,
        address=data.initial_outlet_address,
        payment_timing=data.initial_outlet_payment_timing,
        is_active=True,
    )
    db.add(outlet)

    # 3. Create Owner User
    hashed_pwd = get_password_hash(data.owner_password)
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        full_name=data.owner_full_name,
        email=data.owner_email.lower(),
        password_hash=hashed_pwd,
        is_central_admin=True,
        is_owner=True,
        is_active=True,
    )
    db.add(user)

    # 4. Assign Owner default Manager role to initial outlet
    role = UserOutletRole(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user.id,
        outlet_id=outlet.id,
        role="MANAGER",
    )
    db.add(role)

    # Atomic commit for entire business registration (NFR-013)
    db.commit()
    db.refresh(user)

    # Generate JWT tokens
    claims = {
        "tenant_id": str(tenant.id),
        "email": user.email,
        "is_owner": user.is_owner,
        "is_central_admin": user.is_central_admin,
    }
    access_token = create_access_token(subject=str(user.id), claims=claims)
    refresh_token = create_refresh_token(subject=str(user.id), claims=claims)

    return access_token, refresh_token, user


def authenticate_user(db: Session, data: LoginRequest) -> Tuple[str, str, User]:
    """FR-008: Authenticate user credentials and return access & refresh JWT tokens."""
    query = db.query(User).filter(User.email == data.email.lower())
    if data.tenant_id:
        query = query.filter(User.tenant_id == data.tenant_id)

    users = query.all()
    if not users:
        raise DomainException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Match user by verifying password against available matches
    matched_user: Optional[User] = None
    for candidate in users:
        if verify_password(data.password, candidate.password_hash):
            matched_user = candidate
            break

    if not matched_user:
        raise DomainException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not matched_user.is_active:
        raise DomainException(
            code="USER_INACTIVE",
            message="User account is deactivated. Please contact your administrator.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    claims = {
        "tenant_id": str(matched_user.tenant_id),
        "email": matched_user.email,
        "is_owner": matched_user.is_owner,
        "is_central_admin": matched_user.is_central_admin,
    }
    access_token = create_access_token(subject=str(matched_user.id), claims=claims)
    refresh_token = create_refresh_token(subject=str(matched_user.id), claims=claims)

    return access_token, refresh_token, matched_user


def get_user_me_profile(db: Session, user: User) -> MeResponse:
    """Retrieve full profile of authenticated user including tenant details and outlet permissions."""
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise DomainException(
            code="TENANT_NOT_FOUND",
            message="Tenant not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    outlets = (
        db.query(Outlet)
        .filter(Outlet.tenant_id == user.tenant_id, Outlet.is_active == True)
        .order_by(Outlet.created_at.asc())
        .all()
    )

    roles = (
        db.query(UserOutletRole)
        .filter(UserOutletRole.tenant_id == user.tenant_id, UserOutletRole.user_id == user.id)
        .all()
    )
    roles_by_outlet: Dict[uuid.UUID, List[str]] = {}
    for r in roles:
        roles_by_outlet.setdefault(r.outlet_id, []).append(r.role)

    outlet_infos: List[MeOutletInfo] = []
    for o in outlets:
        assigned_roles = roles_by_outlet.get(o.id, [])
        if user.is_owner:
            if "OWNER" not in assigned_roles:
                assigned_roles = ["OWNER"] + assigned_roles
            outlet_infos.append(
                MeOutletInfo(
                    outlet_id=o.id,
                    outlet_name=o.name,
                    payment_timing=o.payment_timing,
                    roles=assigned_roles,
                )
            )
        elif assigned_roles:
            outlet_infos.append(
                MeOutletInfo(
                    outlet_id=o.id,
                    outlet_name=o.name,
                    payment_timing=o.payment_timing,
                    roles=assigned_roles,
                )
            )

    return MeResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        tenant_name=tenant.name,
        full_name=user.full_name,
        email=user.email,
        is_central_admin=user.is_central_admin,
        is_owner=user.is_owner,
        is_active=user.is_active,
        outlets=outlet_infos,
    )


def create_employee(
    db: Session,
    tenant_id: uuid.UUID,
    data: UserCreate,
    current_user: User,
) -> User:
    """FR-013: Create employee within current tenant."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to register employees",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Only Business Owner can grant is_central_admin (BD-001)
    if data.is_central_admin and not current_user.is_owner:
        raise DomainException(
            code="FORBIDDEN",
            message="Only the Business Owner can grant Central Admin privileges",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Check email duplicate within this tenant
    existing = (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.email == data.email.lower())
        .first()
    )
    if existing:
        raise DomainException(
            code="EMAIL_ALREADY_EXISTS",
            message="An employee with this email already exists in this business",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        full_name=data.full_name,
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        is_central_admin=data.is_central_admin,
        is_owner=False,
        is_active=True,
    )
    db.add(user)

    # Optional initial outlet role
    if data.initial_outlet_id and data.initial_role:
        norm_role = data.initial_role.upper()
        if norm_role not in VALID_ROLES:
            raise DomainException(
                code="INVALID_ROLE",
                message=f"Invalid role '{data.initial_role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        # Verify outlet belongs to tenant
        outlet = (
            db.query(Outlet)
            .filter(Outlet.id == data.initial_outlet_id, Outlet.tenant_id == tenant_id)
            .first()
        )
        if not outlet:
            raise DomainException(
                code="OUTLET_NOT_FOUND",
                message="Initial outlet not found in this business",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        role = UserOutletRole(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user.id,
            outlet_id=outlet.id,
            role=norm_role,
        )
        db.add(role)

    # Log employee creation to audit_logs
    record_audit_log(
        db=db,
        tenant_id=tenant_id,
        actor_id=current_user.id,
        action="CREATE_EMPLOYEE",
        entity_type="USER",
        entity_id=user.id,
        new_values={
            "full_name": user.full_name,
            "email": user.email,
            "is_central_admin": user.is_central_admin,
            "initial_outlet_id": str(data.initial_outlet_id) if data.initial_outlet_id else None,
            "initial_role": data.initial_role,
        },
    )

    db.commit()
    db.refresh(user)
    return user


def list_employees(
    db: Session,
    tenant_id: uuid.UUID,
    is_active: Optional[bool] = None,
) -> List[User]:
    """List employees strictly within the tenant (NFR-003)."""
    query = db.query(User).filter(User.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.order_by(User.created_at.asc()).all()


def get_employee_by_id(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> User:
    """Retrieve employee by id within the tenant."""
    user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == tenant_id)
        .first()
    )
    if not user:
        raise DomainException(
            code="USER_NOT_FOUND",
            message="Employee not found in your business",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return user


def update_employee(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User,
) -> User:
    """FR-014: Update employee details, activate/deactivate, or adjust permissions."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to update employees",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    user = get_employee_by_id(db, tenant_id, user_id)

    # Business Owner cannot be deactivated by another user or accidentally deactivate self
    if user.is_owner and data.is_active is False:
        raise DomainException(
            code="CANNOT_DEACTIVATE_OWNER",
            message="The Business Owner account cannot be deactivated",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if data.full_name is not None:
        user.full_name = data.full_name

    if data.password is not None:
        user.password_hash = get_password_hash(data.password)

    # Central Admin privilege changes require Owner (BD-001)
    if data.is_central_admin is not None and data.is_central_admin != user.is_central_admin:
        if not current_user.is_owner:
            raise DomainException(
                code="FORBIDDEN",
                message="Only the Business Owner can grant or revoke Central Admin privilege",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        old_val = user.is_central_admin
        user.is_central_admin = data.is_central_admin

        record_audit_log(
            db=db,
            tenant_id=tenant_id,
            actor_id=current_user.id,
            action="UPDATE_EMPLOYEE_PRIVILEGE",
            entity_type="USER",
            entity_id=user.id,
            old_values={"is_central_admin": old_val},
            new_values={"is_central_admin": data.is_central_admin},
            reason=data.reason or "Owner updated Central Admin privilege",
        )

    # Activation / Deactivation audit logging (FR-014, BR-027)
    if data.is_active is not None and data.is_active != user.is_active:
        old_active = user.is_active
        user.is_active = data.is_active

        record_audit_log(
            db=db,
            tenant_id=tenant_id,
            actor_id=current_user.id,
            action="UPDATE_EMPLOYEE_STATUS",
            entity_type="USER",
            entity_id=user.id,
            old_values={"is_active": old_active},
            new_values={"is_active": data.is_active},
            reason=data.reason or ("Deactivated employee" if not data.is_active else "Reactivated employee"),
        )

    db.commit()
    db.refresh(user)
    return user


def assign_outlet_role(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: RoleAssignRequest,
    current_user: User,
) -> UserOutletRole:
    """FR-010, FR-011, FR-012: Assign role to employee for a specific outlet."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to assign outlet roles",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    norm_role = data.role.upper()
    if norm_role not in VALID_ROLES:
        raise DomainException(
            code="INVALID_ROLE",
            message=f"Invalid role '{data.role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Ensure target user belongs to this tenant (BR-001, NFR-003)
    user = get_employee_by_id(db, tenant_id, user_id)

    # Ensure target outlet belongs to this tenant (BR-001, NFR-003)
    outlet = (
        db.query(Outlet)
        .filter(Outlet.id == data.outlet_id, Outlet.tenant_id == tenant_id)
        .first()
    )
    if not outlet:
        raise DomainException(
            code="OUTLET_NOT_FOUND",
            message="Outlet not found in your business",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Check if role assignment already exists
    existing = (
        db.query(UserOutletRole)
        .filter(
            UserOutletRole.tenant_id == tenant_id,
            UserOutletRole.user_id == user.id,
            UserOutletRole.outlet_id == outlet.id,
            UserOutletRole.role == norm_role,
        )
        .first()
    )
    if existing:
        return existing

    role = UserOutletRole(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user.id,
        outlet_id=outlet.id,
        role=norm_role,
    )
    db.add(role)

    # Mandatory audit log for employee permission change (BR-027)
    record_audit_log(
        db=db,
        tenant_id=tenant_id,
        outlet_id=outlet.id,
        actor_id=current_user.id,
        action="ASSIGN_OUTLET_ROLE",
        entity_type="USER_OUTLET_ROLE",
        entity_id=role.id,
        new_values={
            "user_id": str(user.id),
            "outlet_id": str(outlet.id),
            "role": norm_role,
        },
        reason="Assigned outlet role to employee",
    )

    db.commit()
    db.refresh(role)
    return role


def revoke_outlet_role(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: User,
) -> None:
    """Revoke a specific outlet role assignment from an employee."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to revoke outlet roles",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    role = (
        db.query(UserOutletRole)
        .filter(
            UserOutletRole.id == role_id,
            UserOutletRole.tenant_id == tenant_id,
            UserOutletRole.user_id == user_id,
        )
        .first()
    )
    if not role:
        raise DomainException(
            code="ROLE_NOT_FOUND",
            message="Role assignment not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Audit log before deletion
    record_audit_log(
        db=db,
        tenant_id=tenant_id,
        outlet_id=role.outlet_id,
        actor_id=current_user.id,
        action="REVOKE_OUTLET_ROLE",
        entity_type="USER_OUTLET_ROLE",
        entity_id=role.id,
        old_values={
            "user_id": str(user_id),
            "outlet_id": str(role.outlet_id),
            "role": role.role,
        },
        reason="Revoked outlet role from employee",
    )

    db.delete(role)
    db.commit()
