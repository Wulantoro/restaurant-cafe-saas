"""Menu module service re-exporting catalog and inventory services."""

from app.modules.catalog.service import (
    create_category,
    list_categories,
    get_category_by_id,
    update_category,
    create_product,
    list_products,
    get_product_by_id,
    update_product,
    create_variant,
    create_addon,
    set_product_recipe,
    get_product_recipe,
    set_outlet_product_availability,
    list_outlet_menu,
    reject_outlet_price_override,
)
from app.modules.inventory.service import (
    create_ingredient,
    list_ingredients,
    get_ingredient_by_id,
    update_ingredient,
)

__all__ = [
    "create_category",
    "list_categories",
    "get_category_by_id",
    "update_category",
    "create_product",
    "list_products",
    "get_product_by_id",
    "update_product",
    "create_variant",
    "create_addon",
    "set_product_recipe",
    "get_product_recipe",
    "set_outlet_product_availability",
    "list_outlet_menu",
    "reject_outlet_price_override",
    "create_ingredient",
    "list_ingredients",
    "get_ingredient_by_id",
    "update_ingredient",
]
