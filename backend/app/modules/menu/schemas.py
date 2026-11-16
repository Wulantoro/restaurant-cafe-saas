"""Menu module schemas re-exported from catalog and inventory schemas."""

from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryOut,
    VariantCreate,
    VariantOut,
    AddonCreate,
    AddonOut,
    ProductCreate,
    ProductUpdate,
    ProductOut,
    RecipeItemCreate,
    RecipeItemOut,
    RecipeSetRequest,
    RecipeOut,
    OutletAvailabilityUpdate,
    OutletAvailabilityOut,
    PriceOverrideRequest,
)
from app.modules.inventory.schemas import (
    IngredientCreate,
    IngredientUpdate,
    IngredientOut,
)

__all__ = [
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryOut",
    "VariantCreate",
    "VariantOut",
    "AddonCreate",
    "AddonOut",
    "ProductCreate",
    "ProductUpdate",
    "ProductOut",
    "RecipeItemCreate",
    "RecipeItemOut",
    "RecipeSetRequest",
    "RecipeOut",
    "OutletAvailabilityUpdate",
    "OutletAvailabilityOut",
    "PriceOverrideRequest",
    "IngredientCreate",
    "IngredientUpdate",
    "IngredientOut",
]
