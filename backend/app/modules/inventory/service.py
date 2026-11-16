import uuid
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import status

from app.core.exceptions import DomainException
from app.modules.inventory.models import Ingredient, InventoryBalance
from app.modules.inventory.schemas import IngredientCreate, IngredientUpdate
from app.modules.tenancy.models import Outlet
from app.modules.iam.models import User


def get_ingredient_by_id(
    db: Session,
    tenant_id: uuid.UUID,
    ingredient_id: uuid.UUID,
) -> Ingredient:
    """Retrieve an ingredient strictly within tenant scope (NFR-003)."""
    ingredient = (
        db.query(Ingredient)
        .filter(Ingredient.id == ingredient_id, Ingredient.tenant_id == tenant_id)
        .first()
    )
    if not ingredient:
        raise DomainException(
            code="INGREDIENT_NOT_FOUND",
            message="Ingredient not found or does not belong to your business",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return ingredient


def create_ingredient(
    db: Session,
    tenant_id: uuid.UUID,
    data: IngredientCreate,
    current_user: User,
) -> Ingredient:
    """FR-063: Create master raw material/ingredient centrally (Central Admin / Owner)."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to create master ingredients",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Check duplicate name within this tenant
    duplicate = (
        db.query(Ingredient)
        .filter(
            Ingredient.tenant_id == tenant_id,
            Ingredient.name.ilike(data.name.strip()),
        )
        .first()
    )
    if duplicate:
        raise DomainException(
            code="DUPLICATE_INGREDIENT",
            message=f"Ingredient '{data.name}' already exists in your business catalog",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    ingredient = Ingredient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=data.name.strip(),
        unit=data.unit.strip(),
        min_stock_threshold=data.min_stock_threshold,
        average_unit_cost=data.average_unit_cost,
        is_active=True,
    )
    db.add(ingredient)

    # Initialize inventory balances across all active outlets for this tenant
    outlets = db.query(Outlet).filter(Outlet.tenant_id == tenant_id).all()
    for outlet in outlets:
        balance = InventoryBalance(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            outlet_id=outlet.id,
            ingredient_id=ingredient.id,
            on_hand_qty=Decimal("0.000"),
            reserved_qty=Decimal("0.000"),
            version=1,
        )
        db.add(balance)

    db.commit()
    db.refresh(ingredient)
    return ingredient


def list_ingredients(
    db: Session,
    tenant_id: uuid.UUID,
    is_active: Optional[bool] = None,
) -> List[Ingredient]:
    """List ingredients strictly isolated to tenant."""
    query = db.query(Ingredient).filter(Ingredient.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(Ingredient.is_active == is_active)
    return query.order_by(Ingredient.name.asc()).all()


def update_ingredient(
    db: Session,
    tenant_id: uuid.UUID,
    ingredient_id: uuid.UUID,
    data: IngredientUpdate,
    current_user: User,
) -> Ingredient:
    """Update master ingredient attributes and average unit cost."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to update master ingredients",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    ingredient = get_ingredient_by_id(db, tenant_id, ingredient_id)

    if data.name is not None:
        norm_name = data.name.strip()
        if norm_name.lower() != ingredient.name.lower():
            dup = (
                db.query(Ingredient)
                .filter(
                    Ingredient.tenant_id == tenant_id,
                    Ingredient.name.ilike(norm_name),
                    Ingredient.id != ingredient_id,
                )
                .first()
            )
            if dup:
                raise DomainException(
                    code="DUPLICATE_INGREDIENT",
                    message=f"Another ingredient named '{data.name}' already exists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        ingredient.name = norm_name

    if data.unit is not None:
        ingredient.unit = data.unit.strip()
    if data.min_stock_threshold is not None:
        ingredient.min_stock_threshold = data.min_stock_threshold
    if data.average_unit_cost is not None:
        ingredient.average_unit_cost = data.average_unit_cost
    if data.is_active is not None:
        ingredient.is_active = data.is_active

    db.commit()
    db.refresh(ingredient)
    return ingredient
