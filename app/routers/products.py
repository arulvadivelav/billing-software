from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def list_products_page(request: Request, db: AsyncSession = Depends(get_db)):
    products = await crud.list_products(db)
    return templates.TemplateResponse("products.html", {"request": request, "products": products, "error": None})


@router.post("")
async def create_product_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    product_id: str = Form(...),
    name: str = Form(...),
    available_stock: int = Form(...),
    price_per_unit: float = Form(...),
    tax_percentage: float = Form(0.0),
):
    existing = await crud.get_product_by_business_id(db, product_id)
    if existing is not None:
        products = await crud.list_products(db)
        return templates.TemplateResponse(
            "products.html",
            {"request": request, "products": products, "error": f"Product ID '{product_id}' already exists."},
            status_code=400,
        )

    data = schemas.ProductCreate(
        product_id=product_id,
        name=name,
        available_stock=available_stock,
        price_per_unit=price_per_unit,
        tax_percentage=tax_percentage,
    )
    await crud.create_product(db, data)
    return RedirectResponse(url="/products", status_code=303)
