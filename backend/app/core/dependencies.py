import uuid
from typing import List, Optional
from fastapi import Depends, Header, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DomainException
from app.core.security import decode_token
from app.modules.iam.models import User, UserOutletRole
from app.modules.tenancy.models import Tenant, Outlet


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the current authenticated user from Bearer JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        raise DomainException(
            code="UNAUTHORIZED",
            message="Missing or invalid Authorization header",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise DomainException(
            code="INVALID_TOKEN",
            message="Invalid token type: access token required",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    sub = payload.get("sub")
    tenant_id_str = payload.get("tenant_id")
    if not sub or not tenant_id_str:
        raise DomainException(
            code="INVALID_TOKEN",
            message="Invalid token payload",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user_id = uuid.UUID(sub)
        tenant_id = uuid.UUID(tenant_id_str)
    except (ValueError, TypeError):
        raise DomainException(
            code="INVALID_TOKEN",
            message="Malformed identifiers in token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Multi-tenant isolation: always query by BOTH user.id and user.tenant_id
    user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == tenant_id, User.is_active == True)
        .first()
    )

    if not user:
        raise DomainException(
            code="USER_NOT_FOUND",
            message="User account is inactive or not found",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return user


def get_current_tenant_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Tenant:
    """Enforce BR-001 & NFR-003: Tenant context is injected exclusively from authenticated user's JWT."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise DomainException(
            code="TENANT_NOT_FOUND",
            message="Business tenant not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return tenant


def require_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    """Guard requiring Business Owner role."""
    if not current_user.is_owner:
        raise DomainException(
            code="FORBIDDEN",
            message="Owner authority is required for this action",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return current_user


def require_central_admin_or_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    """Guard requiring Central Admin or Owner role scoped strictly within the tenant (BD-001)."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority is required for this action",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return current_user


class RequireOutletAccess:
    """Guard verifying user has permission for a specific outlet within their tenant.
    
    Owner has full access to all outlets in their tenant.
    Central Admin has read-only or central management, but if checking outlet operational roles,
    we verify user has one of allowed_roles in user_outlet_roles.
    """

    def __init__(self, *allowed_roles: str):
        self.allowed_roles = [r.upper() for r in allowed_roles]

    def __call__(
        self,
        outlet_id: uuid.UUID = Path(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Outlet:
        # 1. Enforce tenant isolation on outlet
        outlet = (
            db.query(Outlet)
            .filter(Outlet.id == outlet_id, Outlet.tenant_id == current_user.tenant_id)
            .first()
        )
        if not outlet:
            raise DomainException(
                code="OUTLET_NOT_FOUND",
                message="Outlet not found or does not belong to your business",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not outlet.is_active:
            raise DomainException(
                code="OUTLET_INACTIVE",
                message="Outlet is currently inactive",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Business Owner always has full access to all outlets in their tenant
        if current_user.is_owner:
            return outlet

        # 3. Check role assignment for this outlet
        roles_query = (
            db.query(UserOutletRole)
            .filter(
                UserOutletRole.tenant_id == current_user.tenant_id,
                UserOutletRole.user_id == current_user.id,
                UserOutletRole.outlet_id == outlet_id,
            )
            .all()
        )
        user_roles = [r.role.upper() for r in roles_query]

        if not user_roles:
            raise DomainException(
                code="FORBIDDEN",
                message="You do not have access to this outlet",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if self.allowed_roles:
            if not any(role in self.allowed_roles for role in user_roles):
                raise DomainException(
                    code="FORBIDDEN",
                    message=f"Insufficient role permissions for this outlet. Required one of: {', '.join(self.allowed_roles)}",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        return outlet
