from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db

router = APIRouter(prefix="/purchases", tags=["purchases"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def purchase_history_page(request: Request, email: str | None = None, db: AsyncSession = Depends(get_db)):
    purchases = []
    if email:
        purchases = await crud.get_purchases_by_email(db, email.strip())
    return templates.TemplateResponse(
        "purchase_history.html", {"request": request, "purchases": purchases, "email": email or ""}
    )


@router.get("/{purchase_id}")
async def purchase_detail_page(request: Request, purchase_id: int, db: AsyncSession = Depends(get_db)):
    purchase = await crud.get_purchase_detail(db, purchase_id)
    if purchase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase not found.")
    return templates.TemplateResponse("purchase_detail.html", {"request": request, "purchase": purchase})
