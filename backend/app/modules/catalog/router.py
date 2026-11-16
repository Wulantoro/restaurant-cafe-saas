import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.iam.models import User
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryOut,
    ProductCreate,
    ProductUpdate,
    ProductOut,
    VariantCreate,
    VariantOut,
    AddonCreate,
    AddonOut,
    RecipeSetRequest,
    RecipeOut,
    OutletAvailabilityUpdate,
    OutletAvailabilityOut,
    PriceOverrideRequest,
)
from app.modules.catalog import service

router = APIRouter(tags=["Menu & Catalog"])


# ============================================================================
# MENU CATEGORIES ENDPOINTS
# ============================================================================

@router.post("/catalog/categories", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/menu/categories", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-016: Centralized menu category creation (Central Admin / Owner)."""
    category = service.create_category(
        db=db,
        tenant_id=current_user.tenant_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": CategoryOut.model_validate(category).model_dump(mode="json"),
    }


@router.get("/catalog/categories", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/categories", response_model=dict, status_code=status.HTTP_200_OK)
def list_categories(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List menu categories for current tenant."""
    categories = service.list_categories(
        db=db,
        tenant_id=current_user.tenant_id,
        is_active=is_active,
    )
    return {
        "status": "success",
        "data": [CategoryOut.model_validate(c).model_dump(mode="json") for c in categories],
    }


@router.get("/catalog/categories/{category_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/categories/{category_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single category details."""
    category = service.get_category_by_id(
        db=db,
        tenant_id=current_user.tenant_id,
        category_id=category_id,
    )
    return {
        "status": "success",
        "data": CategoryOut.model_validate(category).model_dump(mode="json"),
    }


@router.patch("/catalog/categories/{category_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.patch("/menu/categories/{category_id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update menu category."""
    category = service.update_category(
        db=db,
        tenant_id=current_user.tenant_id,
        category_id=category_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": CategoryOut.model_validate(category).model_dump(mode="json"),
    }


# ============================================================================
# PRODUCTS & MENU ITEMS ENDPOINTS
# ============================================================================

@router.post("/catalog/products", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/menu/products", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/menu/items", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-017, BR-004, BR-005: Create centrally managed product and prices."""
    product = service.create_product(
        db=db,
        tenant_id=current_user.tenant_id,
        data=payload,
        current_user=current_user,
    )
    recipe_data = service.get_product_recipe(db, current_user.tenant_id, product.id)
    out = ProductOut.model_validate(product)
    out.recipe_cost = recipe_data.total_recipe_cost
    out.recipe_items = recipe_data.items
    return {
        "status": "success",
        "data": out.model_dump(mode="json"),
    }


@router.get("/catalog/products", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/products", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/items", response_model=dict, status_code=status.HTTP_200_OK)
def list_products(
    category_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List products belonging strictly to current tenant."""
    products = service.list_products(
        db=db,
        tenant_id=current_user.tenant_id,
        category_id=category_id,
        is_active=is_active,
    )
    result = []
    for p in products:
        recipe_data = service.get_product_recipe(db, current_user.tenant_id, p.id)
        out = ProductOut.model_validate(p)
        out.recipe_cost = recipe_data.total_recipe_cost
        out.recipe_items = recipe_data.items
        result.append(out.model_dump(mode="json"))

    return {
        "status": "success",
        "data": result,
    }


@router.get("/catalog/products/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/products/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/items/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single product details with variants, addons, and recipe cost."""
    product = service.get_product_by_id(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=product_id,
    )
    recipe_data = service.get_product_recipe(db, current_user.tenant_id, product.id)
    out = ProductOut.model_validate(product)
    out.recipe_cost = recipe_data.total_recipe_cost
    out.recipe_items = recipe_data.items
    return {
        "status": "success",
        "data": out.model_dump(mode="json"),
    }


@router.patch("/catalog/products/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.patch("/menu/products/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
@router.patch("/menu/items/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Central Admin updates product and prices (BR-004, BR-005)."""
    product = service.update_product(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=product_id,
        data=payload,
        current_user=current_user,
    )
    recipe_data = service.get_product_recipe(db, current_user.tenant_id, product.id)
    out = ProductOut.model_validate(product)
    out.recipe_cost = recipe_data.total_recipe_cost
    out.recipe_items = recipe_data.items
    return {
        "status": "success",
        "data": out.model_dump(mode="json"),
    }


@router.post("/catalog/products/{product_id}/variants", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/menu/products/{product_id}/variants", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_variant(
    product_id: uuid.UUID,
    payload: VariantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a variant with price delta to product."""
    variant = service.add_product_variant(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=product_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": VariantOut.model_validate(variant).model_dump(mode="json"),
    }


@router.post("/catalog/products/{product_id}/addons", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/menu/products/{product_id}/addons", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_addon(
    product_id: uuid.UUID,
    payload: AddonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an add-on with price to product."""
    addon = service.add_product_addon(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=product_id,
        data=payload,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": AddonOut.model_validate(addon).model_dump(mode="json"),
    }


# ============================================================================
# RECIPES ENDPOINTS (BD-002, FR-022)
# ============================================================================

@router.put("/catalog/products/{product_id}/recipe", response_model=dict, status_code=status.HTTP_200_OK)
@router.put("/menu/products/{product_id}/recipe", response_model=dict, status_code=status.HTTP_200_OK)
@router.put("/menu/items/{product_id}/recipe", response_model=dict, status_code=status.HTTP_200_OK)
def set_recipe(
    product_id: uuid.UUID,
    payload: RecipeSetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """BD-002, FR-022: Configure centralized recipe shared across all outlets."""
    recipe = service.set_product_recipe(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=product_id,
        items=payload.items,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": recipe.model_dump(mode="json"),
    }


@router.get("/catalog/products/{product_id}/recipe", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/products/{product_id}/recipe", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/menu/items/{product_id}/recipe", response_model=dict, status_code=status.HTTP_200_OK)
def get_recipe(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recipe composition and calculated food cost (FR-086)."""
    recipe = service.get_product_recipe(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=product_id,
    )
    return {
        "status": "success",
        "data": recipe.model_dump(mode="json"),
    }


# ============================================================================
# OUTLET AVAILABILITY & PRICE OVERRIDES (FR-021, BR-005)
# ============================================================================

@router.patch("/outlets/{outlet_id}/products/{product_id}/availability", response_model=dict, status_code=status.HTTP_200_OK)
@router.patch("/outlets/{outlet_id}/items/{product_id}/availability", response_model=dict, status_code=status.HTTP_200_OK)
def update_outlet_availability(
    outlet_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: OutletAvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-021: Toggle local product availability subject to central policy."""
    availability = service.set_outlet_product_availability(
        db=db,
        tenant_id=current_user.tenant_id,
        outlet_id=outlet_id,
        product_id=product_id,
        is_available=payload.is_available,
        current_user=current_user,
    )
    return {
        "status": "success",
        "data": availability.model_dump(mode="json"),
    }


@router.get("/outlets/{outlet_id}/products", response_model=dict, status_code=status.HTTP_200_OK)
@router.get("/outlets/{outlet_id}/menu", response_model=dict, status_code=status.HTTP_200_OK)
def get_outlet_menu(
    outlet_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all products for an outlet with their effective local availability."""
    items = service.list_outlet_menu(
        db=db,
        tenant_id=current_user.tenant_id,
        outlet_id=outlet_id,
    )
    return {
        "status": "success",
        "data": items,
    }


@router.post("/outlets/{outlet_id}/products/{product_id}/price-override", response_model=dict, status_code=status.HTTP_403_FORBIDDEN)
@router.patch("/outlets/{outlet_id}/products/{product_id}/price-override", response_model=dict, status_code=status.HTTP_403_FORBIDDEN)
@router.post("/outlets/{outlet_id}/items/{product_id}/price-override", response_model=dict, status_code=status.HTTP_403_FORBIDDEN)
@router.patch("/outlets/{outlet_id}/items/{product_id}/price-override", response_model=dict, status_code=status.HTTP_403_FORBIDDEN)
@router.patch("/outlets/{outlet_id}/products/{product_id}/price", response_model=dict, status_code=status.HTTP_403_FORBIDDEN)
def outlet_price_override_rejected(
    outlet_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: Optional[PriceOverrideRequest] = None,
    current_user: User = Depends(get_current_user),
):
    """BR-005: Outlets are strictly forbidden from independently modifying centrally managed prices."""
    service.reject_outlet_price_override(
        tenant_id=current_user.tenant_id,
        outlet_id=outlet_id,
        product_id=product_id,
        current_user=current_user,
    )
