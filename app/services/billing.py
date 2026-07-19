import math

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.services.denomination import InsufficientChangeError, compute_change_breakdown


async def generate_bill(db: AsyncSession, request: schemas.BillGenerateRequest) -> schemas.BillResult:
    if not request.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one product must be added to the bill.")

    line_items: list[dict] = []
    total_price_without_tax = 0.0
    total_tax_payable = 0.0

    for item in request.items:
        product = await crud.get_product_by_business_id(db, item.product_id)
        if product is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Product '{item.product_id}' not found.")
        if product.available_stock < item.quantity:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Insufficient stock for '{product.name}' ({product.product_id}). "
                f"Requested {item.quantity}, available {product.available_stock}.",
            )

        purchase_price = round(product.price_per_unit * item.quantity, 2)
        tax_payable = round(purchase_price * product.tax_percentage / 100, 2)
        total_price = round(purchase_price + tax_payable, 2)

        total_price_without_tax += purchase_price
        total_tax_payable += tax_payable

        line_items.append(
            {
                "product_pk": product.id,
                "product_id": product.product_id,
                "product_name": product.name,
                "unit_price": product.price_per_unit,
                "tax_percentage": product.tax_percentage,
                "quantity": item.quantity,
                "purchase_price": purchase_price,
                "tax_payable": tax_payable,
                "total_price": total_price,
                "_product_obj": product,
            }
        )

    total_price_without_tax = round(total_price_without_tax, 2)
    total_tax_payable = round(total_tax_payable, 2)
    net_price = round(total_price_without_tax + total_tax_payable, 2)
    rounded_net_price = float(math.floor(net_price))

    if request.cash_paid < rounded_net_price:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cash paid ({request.cash_paid}) is less than the amount payable ({rounded_net_price}).",
        )

    balance_amount = round(request.cash_paid - rounded_net_price, 2)

    denom_counts_in = {d.value: d.count for d in request.denomination_counts}
    await crud.upsert_denomination_counts(db, denom_counts_in)

    try:
        change_breakdown = compute_change_breakdown(balance_amount, denom_counts_in)
    except InsufficientChangeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    for li in line_items:
        await crud.decrement_stock(db, li.pop("_product_obj"), li["quantity"])

    await crud.apply_change_given(db, change_breakdown)

    totals = {
        "total_price_without_tax": total_price_without_tax,
        "total_tax_payable": total_tax_payable,
        "net_price": net_price,
        "rounded_net_price": rounded_net_price,
        "cash_paid": request.cash_paid,
        "balance_amount": balance_amount,
    }

    purchase = await crud.create_purchase(
        db,
        customer_email=request.customer_email,
        totals=totals,
        line_items=line_items,
        change_breakdown=change_breakdown,
    )

    return schemas.BillResult(
        purchase_id=purchase.id,
        customer_email=purchase.customer_email,
        items=[
            schemas.BillItemOut(
                product_id=li["product_id"],
                product_name=li["product_name"],
                unit_price=li["unit_price"],
                quantity=li["quantity"],
                purchase_price=li["purchase_price"],
                tax_percentage=li["tax_percentage"],
                tax_payable=li["tax_payable"],
                total_price=li["total_price"],
            )
            for li in line_items
        ],
        total_price_without_tax=total_price_without_tax,
        total_tax_payable=total_tax_payable,
        net_price=net_price,
        rounded_net_price=rounded_net_price,
        cash_paid=request.cash_paid,
        balance_amount=balance_amount,
        change_denominations=[
            schemas.ChangeDenominationOut(value=v, count=c)
            for v, c in sorted(change_breakdown.items(), reverse=True)
        ],
        created_at=purchase.created_at,
    )
