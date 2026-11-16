import uuid
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import status

from app.core.exceptions import DomainException
from app.modules.catalog.models import (
    MenuCategory,
    Product,
    ProductVariant,
    ProductAddon,
    OutletProductAvailability,
)
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    AddonCreate,
    RecipeItemCreate,
    RecipeItemOut,
    RecipeOut,
    OutletAvailabilityOut,
)
from app.modules.inventory.models import Ingredient, RecipeItem
from app.modules.tenancy.models import Outlet
from app.modules.iam.models import User, UserOutletRole


# ============================================================================
# CATEGORIES SERVICE
# ============================================================================

def get_category_by_id(db: Session, tenant_id: uuid.UUID, category_id: uuid.UUID) -> MenuCategory:
    category = (
        db.query(MenuCategory)
        .filter(MenuCategory.id == category_id, MenuCategory.tenant_id == tenant_id)
        .first()
    )
    if not category:
        raise DomainException(
            code="CATEGORY_NOT_FOUND",
            message="Menu category not found in your business",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return category


def create_category(
    db: Session,
    tenant_id: uuid.UUID,
    data: CategoryCreate,
    current_user: User,
) -> MenuCategory:
    """FR-016: Centralized menu category creation (Central Admin / Owner)."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to manage menu categories",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Check duplicate category name within this tenant
    dup = (
        db.query(MenuCategory)
        .filter(
            MenuCategory.tenant_id == tenant_id,
            MenuCategory.name.ilike(data.name.strip()),
        )
        .first()
    )
    if dup:
        raise DomainException(
            code="DUPLICATE_CATEGORY",
            message=f"Category '{data.name}' already exists in your business menu",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    category = MenuCategory(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=data.name.strip(),
        sort_order=data.sort_order,
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def list_categories(
    db: Session,
    tenant_id: uuid.UUID,
    is_active: Optional[bool] = None,
) -> List[MenuCategory]:
    query = db.query(MenuCategory).filter(MenuCategory.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(MenuCategory.is_active == is_active)
    return query.order_by(MenuCategory.sort_order.asc(), MenuCategory.name.asc()).all()


def update_category(
    db: Session,
    tenant_id: uuid.UUID,
    category_id: uuid.UUID,
    data: CategoryUpdate,
    current_user: User,
) -> MenuCategory:
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to update menu categories",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    category = get_category_by_id(db, tenant_id, category_id)

    if data.name is not None:
        norm_name = data.name.strip()
        if norm_name.lower() != category.name.lower():
            dup = (
                db.query(MenuCategory)
                .filter(
                    MenuCategory.tenant_id == tenant_id,
                    MenuCategory.name.ilike(norm_name),
                    MenuCategory.id != category_id,
                )
                .first()
            )
            if dup:
                raise DomainException(
                    code="DUPLICATE_CATEGORY",
                    message=f"Category '{data.name}' already exists in your business menu",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        category.name = norm_name

    if data.sort_order is not None:
        category.sort_order = data.sort_order
    if data.is_active is not None:
        category.is_active = data.is_active

    db.commit()
    db.refresh(category)
    return category


# ============================================================================
# PRODUCTS & MENU ITEMS SERVICE
# ============================================================================

def get_product_by_id(db: Session, tenant_id: uuid.UUID, product_id: uuid.UUID) -> Product:
    """Retrieve product strictly within tenant scope."""
    product = (
        db.query(Product)
        .options(
            joinedload(Product.variants),
            joinedload(Product.addons),
            joinedload(Product.recipe_items).joinedload(RecipeItem.ingredient),
        )
        .filter(Product.id == product_id, Product.tenant_id == tenant_id)
        .first()
    )
    if not product:
        raise DomainException(
            code="PRODUCT_NOT_FOUND",
            message="Product not found in your business catalog",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return product


def create_product(
    db: Session,
    tenant_id: uuid.UUID,
    data: ProductCreate,
    current_user: User,
) -> Product:
    """FR-017, BR-004, BR-005: Create centrally managed product and pricing."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to create products and prices (BR-005)",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 1. Verify Category exists and belongs to this tenant
    get_category_by_id(db, tenant_id, data.category_id)

    # 2. Check duplicate product name in this tenant
    dup = (
        db.query(Product)
        .filter(
            Product.tenant_id == tenant_id,
            Product.name.ilike(data.name.strip()),
        )
        .first()
    )
    if dup:
        raise DomainException(
            code="DUPLICATE_PRODUCT",
            message=f"Product with name '{data.name}' already exists in your business",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    product = Product(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        category_id=data.category_id,
        name=data.name.strip(),
        description=data.description,
        base_price=data.base_price,
        allow_outlet_availability_override=data.allow_outlet_availability_override,
        is_active=True,
    )
    db.add(product)

    # 3. Optional initial variants (FR-018)
    variant_map: Dict[str, ProductVariant] = {}
    if data.variants:
        for v in data.variants:
            variant = ProductVariant(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                product_id=product.id,
                name=v.name.strip(),
                price_delta=v.price_delta,
                is_active=True,
            )
            db.add(variant)
            variant_map[v.name.strip()] = variant

    # 4. Optional initial addons (FR-019)
    if data.addons:
        for a in data.addons:
            addon = ProductAddon(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                product_id=product.id,
                name=a.name.strip(),
                price=a.price,
                is_active=True,
            )
            db.add(addon)

    # 5. Optional initial recipe items (BD-002)
    if data.recipe_items:
        for item in data.recipe_items:
            # Validate ingredient belongs to tenant
            ingredient = (
                db.query(Ingredient)
                .filter(Ingredient.id == item.ingredient_id, Ingredient.tenant_id == tenant_id)
                .first()
            )
            if not ingredient:
                raise DomainException(
                    code="INGREDIENT_NOT_FOUND",
                    message=f"Ingredient ID '{item.ingredient_id}' not found in your business",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            recipe_item = RecipeItem(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                product_id=product.id,
                variant_id=item.variant_id,
                ingredient_id=item.ingredient_id,
                quantity_required=item.quantity_required,
            )
            db.add(recipe_item)

    db.commit()
    db.refresh(product)
    return get_product_by_id(db, tenant_id, product.id)


def list_products(
    db: Session,
    tenant_id: uuid.UUID,
    category_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
) -> List[Product]:
    query = (
        db.query(Product)
        .options(
            joinedload(Product.variants),
            joinedload(Product.addons),
            joinedload(Product.recipe_items).joinedload(RecipeItem.ingredient),
        )
        .filter(Product.tenant_id == tenant_id)
    )
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    return query.order_by(Product.name.asc()).all()


def update_product(
    db: Session,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    data: ProductUpdate,
    current_user: User,
) -> Product:
    """Central Admin updates product and centralized pricing (BR-004, BR-005)."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to modify product definition or prices (BR-005)",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    product = get_product_by_id(db, tenant_id, product_id)

    if data.category_id is not None:
        get_category_by_id(db, tenant_id, data.category_id)
        product.category_id = data.category_id

    if data.name is not None:
        norm_name = data.name.strip()
        if norm_name.lower() != product.name.lower():
            dup = (
                db.query(Product)
                .filter(
                    Product.tenant_id == tenant_id,
                    Product.name.ilike(norm_name),
                    Product.id != product_id,
                )
                .first()
            )
            if dup:
                raise DomainException(
                    code="DUPLICATE_PRODUCT",
                    message=f"Product with name '{data.name}' already exists in your business",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        product.name = norm_name

    if data.description is not None:
        product.description = data.description
    if data.base_price is not None:
        product.base_price = data.base_price
    if data.allow_outlet_availability_override is not None:
        product.allow_outlet_availability_override = data.allow_outlet_availability_override
    if data.is_active is not None:
        product.is_active = data.is_active

    db.commit()
    db.refresh(product)
    return product


def add_product_variant(
    db: Session,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    data: VariantCreate,
    current_user: User,
) -> ProductVariant:
    """FR-018: Add variant to product."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to add product variants",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    product = get_product_by_id(db, tenant_id, product_id)
    variant = ProductVariant(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product.id,
        name=data.name.strip(),
        price_delta=data.price_delta,
        is_active=True,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def add_product_addon(
    db: Session,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    data: AddonCreate,
    current_user: User,
) -> ProductAddon:
    """FR-019: Add addon to product."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to add product add-ons",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    product = get_product_by_id(db, tenant_id, product_id)
    addon = ProductAddon(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product.id,
        name=data.name.strip(),
        price=data.price,
        is_active=True,
    )
    db.add(addon)
    db.commit()
    db.refresh(addon)
    return addon


# ============================================================================
# RECIPES SERVICE (BD-002, FR-022, FR-086)
# ============================================================================

def set_product_recipe(
    db: Session,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    items: List[RecipeItemCreate],
    current_user: User,
) -> RecipeOut:
    """BD-002, FR-022: Configure centralized recipe shared across all outlets."""
    if not (current_user.is_owner or current_user.is_central_admin):
        raise DomainException(
            code="FORBIDDEN",
            message="Central Admin or Owner authority required to configure centralized recipes (BD-002)",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    product = get_product_by_id(db, tenant_id, product_id)

    # 1. Validate all ingredients and variants belong to this tenant
    for item in items:
        ingredient = (
            db.query(Ingredient)
            .filter(Ingredient.id == item.ingredient_id, Ingredient.tenant_id == tenant_id)
            .first()
        )
        if not ingredient:
            raise DomainException(
                code="INGREDIENT_NOT_FOUND",
                message=f"Ingredient ID '{item.ingredient_id}' not found in your business",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if item.variant_id:
            variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.id == item.variant_id,
                    ProductVariant.product_id == product.id,
                    ProductVariant.tenant_id == tenant_id,
                )
                .first()
            )
            if not variant:
                raise DomainException(
                    code="VARIANT_NOT_FOUND",
                    message=f"Variant ID '{item.variant_id}' does not belong to product '{product.name}'",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

    # 2. Clear existing recipe items and replace atomically
    db.query(RecipeItem).filter(
        RecipeItem.tenant_id == tenant_id,
        RecipeItem.product_id == product.id,
    ).delete(synchronize_session=False)

    for item in items:
        ri = RecipeItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            product_id=product.id,
            variant_id=item.variant_id,
            ingredient_id=item.ingredient_id,
            quantity_required=item.quantity_required,
        )
        db.add(ri)

    db.commit()
    return get_product_recipe(db, tenant_id, product_id)


def get_product_recipe(
    db: Session,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
) -> RecipeOut:
    """Retrieve recipe details and calculate recipe food cost (FR-086)."""
    product = get_product_by_id(db, tenant_id, product_id)

    recipe_items = (
        db.query(RecipeItem)
        .options(
            joinedload(RecipeItem.ingredient),
            joinedload(RecipeItem.variant),
        )
        .filter(
            RecipeItem.tenant_id == tenant_id,
            RecipeItem.product_id == product.id,
        )
        .all()
    )

    out_items: List[RecipeItemOut] = []
    total_cost = Decimal("0.00")

    for ri in recipe_items:
        ing_cost = ri.ingredient.average_unit_cost or Decimal("0.00")
        item_cost = Decimal(str(ri.quantity_required)) * Decimal(str(ing_cost))
        total_cost += item_cost

        out_items.append(
            RecipeItemOut(
                id=ri.id,
                ingredient_id=ri.ingredient_id,
                ingredient_name=ri.ingredient.name,
                unit=ri.ingredient.unit,
                quantity_required=ri.quantity_required,
                average_unit_cost=ing_cost,
                item_cost=item_cost,
                variant_id=ri.variant_id,
                variant_name=ri.variant.name if ri.variant else None,
            )
        )

    return RecipeOut(
        product_id=product.id,
        product_name=product.name,
        base_price=product.base_price,
        total_recipe_cost=total_cost,
        items=out_items,
    )


# ============================================================================
# OUTLET PRODUCT AVAILABILITY & PRICE OVERRIDES (FR-021, BR-005)
# ============================================================================

def set_outlet_product_availability(
    db: Session,
    tenant_id: uuid.UUID,
    outlet_id: uuid.UUID,
    product_id: uuid.UUID,
    is_available: bool,
    current_user: User,
) -> OutletAvailabilityOut:
    """FR-021: Toggle local product availability subject to central policy."""
    # 1. Verify outlet belongs to tenant
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

    # 2. Verify user has permission for this outlet (or is Owner / Central Admin)
    if not (current_user.is_owner or current_user.is_central_admin):
        has_role = (
            db.query(UserOutletRole)
            .filter(
                UserOutletRole.tenant_id == tenant_id,
                UserOutletRole.outlet_id == outlet_id,
                UserOutletRole.user_id == current_user.id,
            )
            .first()
        )
        if not has_role:
            raise DomainException(
                code="FORBIDDEN",
                message="You do not have access to manage availability for this outlet",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # 3. Verify product belongs to tenant
    product = get_product_by_id(db, tenant_id, product_id)

    # 4. Check if central policy allows outlet availability override
    if not product.allow_outlet_availability_override:
        raise DomainException(
            code="OVERRIDE_NOT_ALLOWED",
            message="Central menu policy does not allow outlet availability override for this product (FR-021)",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 5. Upsert outlet product availability
    avail = (
        db.query(OutletProductAvailability)
        .filter(
            OutletProductAvailability.tenant_id == tenant_id,
            OutletProductAvailability.outlet_id == outlet_id,
            OutletProductAvailability.product_id == product_id,
        )
        .first()
    )
    if not avail:
        avail = OutletProductAvailability(
            tenant_id=tenant_id,
            outlet_id=outlet_id,
            product_id=product_id,
            is_available=is_available,
        )
        db.add(avail)
    else:
        avail.is_available = is_available

    db.commit()
    db.refresh(avail)

    return OutletAvailabilityOut(
        outlet_id=outlet.id,
        product_id=product.id,
        product_name=product.name,
        base_price=product.base_price,
        is_available=avail.is_available,
        allow_outlet_availability_override=product.allow_outlet_availability_override,
        updated_at=avail.updated_at,
    )


def reject_outlet_price_override(
    tenant_id: uuid.UUID,
    outlet_id: uuid.UUID,
    product_id: uuid.UUID,
    current_user: User,
) -> None:
    """BR-005, BD-001: Strict rejection of outlet-specific price overrides."""
    raise DomainException(
        code="PRICE_OVERRIDE_NOT_ALLOWED",
        message="Outlets cannot independently modify centrally managed product prices (BR-005)",
        status_code=status.HTTP_403_FORBIDDEN,
    )


def list_outlet_menu(
    db: Session,
    tenant_id: uuid.UUID,
    outlet_id: uuid.UUID,
) -> List[Dict[str, Any]]:
    """List all products for an outlet with their effective local availability."""
    outlet = (
        db.query(Outlet)
        .filter(Outlet.id == outlet_id, Outlet.tenant_id == tenant_id)
        .first()
    )
    if not outlet:
        raise DomainException(
            code="OUTLET_NOT_FOUND",
            message="Outlet not found in your business",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    products = (
        db.query(Product)
        .options(joinedload(Product.variants), joinedload(Product.addons))
        .filter(Product.tenant_id == tenant_id, Product.is_active == True)
        .order_by(Product.name.asc())
        .all()
    )

    overrides = (
        db.query(OutletProductAvailability)
        .filter(
            OutletProductAvailability.tenant_id == tenant_id,
            OutletProductAvailability.outlet_id == outlet_id,
        )
        .all()
    )
    avail_map = {o.product_id: o.is_available for o in overrides}

    items = []
    for p in products:
        # Default is available unless locally overridden to false
        is_avail = avail_map.get(p.id, True)
        items.append({
            "id": p.id,
            "category_id": p.category_id,
            "name": p.name,
            "description": p.description,
            "base_price": p.base_price,
            "is_available": is_avail,
            "allow_outlet_availability_override": p.allow_outlet_availability_override,
            "variants": [{"id": v.id, "name": v.name, "price_delta": v.price_delta} for v in p.variants if v.is_active],
            "addons": [{"id": a.id, "name": a.name, "price": a.price} for a in p.addons if a.is_active],
        })
    return items
