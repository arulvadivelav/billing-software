from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas


async def get_product_by_business_id(db: AsyncSession, product_id: str) -> models.Product | None:
    result = await db.execute(select(models.Product).where(models.Product.product_id == product_id))
    return result.scalar_one_or_none()


async def list_products(db: AsyncSession) -> list[models.Product]:
    result = await db.execute(select(models.Product).order_by(models.Product.name))
    return list(result.scalars().all())


async def create_product(db: AsyncSession, data: schemas.ProductCreate) -> models.Product:
    product = models.Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def decrement_stock(db: AsyncSession, product: models.Product, quantity: int) -> None:
    product.available_stock -= quantity
    db.add(product)


async def list_denominations(db: AsyncSession) -> list[models.Denomination]:
    result = await db.execute(select(models.Denomination).order_by(models.Denomination.value.desc()))
    return list(result.scalars().all())


async def upsert_denomination_counts(db: AsyncSession, counts: dict[int, int]) -> None:
    existing = {d.value: d for d in await list_denominations(db)}
    for value, count in counts.items():
        if value in existing:
            existing[value].available_count = count
            db.add(existing[value])
        else:
            db.add(models.Denomination(value=value, available_count=count))
    await db.flush()


async def apply_change_given(db: AsyncSession, change: dict[int, int]) -> None:
    existing = {d.value: d for d in await list_denominations(db)}
    for value, count in change.items():
        if count <= 0:
            continue
        denom = existing.get(value)
        if denom is None:
            continue
        denom.available_count -= count
        db.add(denom)


async def create_purchase(
    db: AsyncSession,
    customer_email: str,
    totals: dict,
    line_items: list[dict],
    change_breakdown: dict[int, int],
) -> models.Purchase:
    purchase = models.Purchase(
        customer_email=customer_email,
        total_price_without_tax=totals["total_price_without_tax"],
        total_tax_payable=totals["total_tax_payable"],
        net_price=totals["net_price"],
        rounded_net_price=totals["rounded_net_price"],
        cash_paid=totals["cash_paid"],
        balance_amount=totals["balance_amount"],
        created_at=dt.datetime.now(dt.timezone.utc),
    )
    db.add(purchase)
    await db.flush()

    for li in line_items:
        db.add(
            models.PurchaseItem(
                purchase_id=purchase.id,
                product_id=li["product_pk"],
                product_business_id=li["product_id"],
                product_name=li["product_name"],
                unit_price=li["unit_price"],
                tax_percentage=li["tax_percentage"],
                quantity=li["quantity"],
                purchase_price=li["purchase_price"],
                tax_payable=li["tax_payable"],
                total_price=li["total_price"],
            )
        )

    for value, count in change_breakdown.items():
        if count > 0:
            db.add(
                models.PurchaseChangeGiven(
                    purchase_id=purchase.id, denomination_value=value, count=count
                )
            )

    await db.commit()
    await db.refresh(purchase)
    return purchase


async def get_purchases_by_email(db: AsyncSession, email: str) -> list[models.Purchase]:
    result = await db.execute(
        select(models.Purchase)
        .where(models.Purchase.customer_email == email)
        .order_by(models.Purchase.created_at.desc())
    )
    return list(result.scalars().all())


async def get_purchase_detail(db: AsyncSession, purchase_id: int) -> models.Purchase | None:
    result = await db.execute(select(models.Purchase).where(models.Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if purchase is None:
        return None
    await db.refresh(purchase, attribute_names=["items", "change_given"])
    return purchase
