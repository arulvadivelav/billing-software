from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app import crud
from app.routers import billing, products, purchases


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        existing = await crud.list_denominations(db)
        if not existing:
            await crud.upsert_denomination_counts(db, {value: 0 for value in settings.default_denomination_values})
            await db.commit()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(billing.router)
app.include_router(products.router)
app.include_router(purchases.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/billing")
