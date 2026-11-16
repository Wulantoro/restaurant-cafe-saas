import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.iam.models import User
from app.modules.inventory.schemas import IngredientCreate, IngredientUpdate, IngredientOut
from app.modules.inventory import service

router = APIRouter(tags=["Inventory Master Data"])


@router.post("/inventory/ingredients", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    payload: IngredientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-063: Create master ingredient/raw material (Central Admin / Owner)."""
    ingredient = service.create_ingredient(
        db=db,
        tenant_id=current_user.tenant_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": IngredientOut.model_validate(ingredient).model_dump(mode="json"),
    }


@router.get("/inventory/ingredients", response_model=dict, status_code=status.HTTP_200_OK)
def list_ingredients(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List master raw materials belonging strictly to authenticated tenant."""
    ingredients = service.list_ingredients(
        db=db,
        tenant_id=current_user.tenant_id,
        is_active=is_active,
    )
    return {
        "status": "success",
        "data": [IngredientOut.model_validate(i).model_dump(mode="json") for i in ingredients],
    }


@router.get("/inventory/ingredients/{ingredient_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_ingredient(
    ingredient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single ingredient detail."""
    ingredient = service.get_ingredient_by_id(
        db=db,
        tenant_id=current_user.tenant_id,
        ingredient_id=ingredient_id,
    )
    return {
        "status": "success",
        "data": IngredientOut.model_validate(ingredient).model_dump(mode="json"),
    }


@router.patch("/inventory/ingredients/{ingredient_id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_ingredient(
    ingredient_id: uuid.UUID,
    payload: IngredientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update master ingredient attributes and costs."""
    ingredient = service.update_ingredient(
        db=db,
        tenant_id=current_user.tenant_id,
        ingredient_id=ingredient_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": IngredientOut.model_validate(ingredient).model_dump(mode="json"),
    }
