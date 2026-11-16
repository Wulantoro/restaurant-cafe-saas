import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_central_admin_or_owner
from app.modules.iam.models import User
from app.modules.iam.schemas import (
    RegisterBusinessRequest,
    LoginRequest,
    UserOut,
    UserCreate,
    UserUpdate,
    RoleAssignRequest,
    RoleOut,
    MeResponse,
)
from app.modules.iam import service

router = APIRouter(tags=["IAM & Authentication"])


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/auth/register-business", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_business(
    payload: RegisterBusinessRequest,
    db: Session = Depends(get_db),
):
    """FR-001, FR-002: Register a new business with initial tenant, outlet, and owner account."""
    access_token, refresh_token, user = service.register_business(db, payload)
    return {
        "status": "success",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserOut.model_validate(user).model_dump(mode="json"),
        },
    }


@router.post("/auth/login", response_model=dict, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """FR-008: Authenticate user via email and password, returning JWT tokens."""
    access_token, refresh_token, user = service.authenticate_user(db, payload)
    return {
        "status": "success",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserOut.model_validate(user).model_dump(mode="json"),
        },
    }


@router.get("/auth/me", response_model=dict, status_code=status.HTTP_200_OK)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full profile of authenticated user, active tenant, and assigned outlet roles."""
    profile = service.get_user_me_profile(db, current_user)
    return {
        "status": "success",
        "data": profile.model_dump(mode="json"),
    }


# ============================================================================
# EMPLOYEE / USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/employees", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-013: Create employee within current tenant (Central Admin / Owner)."""
    user = service.create_employee(
        db=db,
        tenant_id=current_user.tenant_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": UserOut.model_validate(user).model_dump(mode="json"),
    }


@router.get("/users", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/employees", response_model=dict, status_code=status.HTTP_200_OK)
def list_employees(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all employees belonging to the authenticated tenant (NFR-003)."""
    users = service.list_employees(
        db=db,
        tenant_id=current_user.tenant_id,
        is_active=is_active,
    )
    return {
        "status": "success",
        "data": [UserOut.model_validate(u).model_dump(mode="json") for u in users],
    }


@router.get("/users/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/employees/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_employee(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details of a specific employee within the current tenant."""
    user = service.get_employee_by_id(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=user_id,
    )
    return {
        "status": "success",
        "data": UserOut.model_validate(user).model_dump(mode="json"),
    }


@router.patch("/users/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.patch("/employees/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_employee(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-014: Update employee details, activate/deactivate, or adjust privilege."""
    user = service.update_employee(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=user_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": UserOut.model_validate(user).model_dump(mode="json"),
    }


# ============================================================================
# ROLE ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/users/{user_id}/roles", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/employees/{user_id}/roles", response_model=dict, status_code=status.HTTP_201_CREATED)
def assign_role(
    user_id: uuid.UUID,
    payload: RoleAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-010, FR-011: Assign an outlet operational role to an employee."""
    role = service.assign_outlet_role(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=user_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": RoleOut.model_validate(role).model_dump(mode="json"),
    }


@router.delete("/users/{user_id}/roles/{role_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.delete("/employees/{user_id}/roles/{role_id}", response_model=dict, status_code=status.HTTP_200_OK)
def revoke_role(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke an outlet operational role assignment from an employee."""
    service.revoke_outlet_role(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=user_id,
        role_id=role_id,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": {"message": "Role assignment revoked successfully"},
    }
