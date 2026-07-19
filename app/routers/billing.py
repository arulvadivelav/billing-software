from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db
from app.services.billing import generate_bill
from app.services.email_service import send_invoice_email

router = APIRouter(prefix="/billing", tags=["billing"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def billing_form(request: Request, db: AsyncSession = Depends(get_db)):
    denominations = await crud.list_denominations(db)
    return templates.TemplateResponse(
        "billing_form.html", {"request": request, "denominations": denominations, "error": None}
    )


@router.post("/generate")
async def generate_bill_endpoint(
    request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    form = await request.form()

    customer_email = (form.get("customer_email") or "").strip()

    product_ids = [v for v in form.getlist("product_id[]") if v.strip()]
    quantities = form.getlist("quantity[]")

    items = []
    for pid, qty in zip(product_ids, quantities):
        if not pid.strip():
            continue
        try:
            qty_int = int(qty)
        except (TypeError, ValueError):
            qty_int = 0
        if qty_int > 0:
            items.append(schemas.BillItemIn(product_id=pid.strip(), quantity=qty_int))

    denom_values = form.getlist("denom_value[]")
    denom_counts = form.getlist("denom_count[]")
    denomination_counts = []
    for val, cnt in zip(denom_values, denom_counts):
        try:
            denomination_counts.append(schemas.DenominationCountIn(value=int(val), count=int(cnt or 0)))
        except (TypeError, ValueError):
            continue

    try:
        cash_paid = float(form.get("cash_paid") or 0)
    except ValueError:
        cash_paid = 0.0

    try:
        bill_request = schemas.BillGenerateRequest(
            customer_email=customer_email,
            items=items,
            denomination_counts=denomination_counts,
            cash_paid=cash_paid,
        )
    except Exception as exc:
        denominations = await crud.list_denominations(db)
        return templates.TemplateResponse(
            "billing_form.html",
            {"request": request, "denominations": denominations, "error": str(exc)},
            status_code=400,
        )

    try:
        bill = await generate_bill(db, bill_request)
    except HTTPException as exc:
        denominations = await crud.list_denominations(db)
        return templates.TemplateResponse(
            "billing_form.html",
            {"request": request, "denominations": denominations, "error": exc.detail},
            status_code=exc.status_code,
        )

    background_tasks.add_task(send_invoice_email, bill)

    return templates.TemplateResponse("bill_result.html", {"request": request, "bill": bill})
