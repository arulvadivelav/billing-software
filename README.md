# Billing System — FastAPI Mini Project

Implements the billing task: Page 1 (billing form), Page 2 (generated bill with
change denomination breakdown), and a purchase history lookup.

Stack: **FastAPI**, **SQLAlchemy 2.0 (async)**, **Jinja2**, **Pydantic v2**.
Works with **SQLite** (default, zero-config) or **PostgreSQL** — just change `DATABASE_URL`.

## Layout

```
app/
  main.py, config.py, database.py, models.py, schemas.py, crud.py
  services/billing.py        # bill calculation logic
  services/denomination.py   # change-denomination breakdown
  services/email_service.py  # async invoice email (BackgroundTask)
  routers/billing.py         # Page 1 + Page 2
  routers/products.py        # product CRUD
  routers/purchases.py       # purchase history
  templates/                 # Jinja2 HTML
seed.py
requirements.txt
```

## Schema

- **Product**: product_id, name, available_stock, price_per_unit, tax_percentage
- **Denomination**: value, available_count (shop's current cash-drawer stock)
- **Purchase / PurchaseItem / PurchaseChangeGiven**: one bill, its line items, and the change given

## Run

```bash
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

- `/billing` — generate a bill
- `/products` — add/view products
- `/purchases?email=...` — purchase history

To use PostgreSQL, set in `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/billing_db
```

## Assumptions

1. The denomination counts entered on the billing form are the shop's current
   cash-drawer stock, re-confirmed at billing time; they're saved and then
   used (and decremented) to compute the change breakdown.
2. "Rounded down value" = floor to the nearest whole currency unit
   (e.g. 2357.60 -> 2357.00), matching the sample in the task doc.
3. If the shop's denominations can't make exact change, the request is
   rejected with an error instead of over/under-paying the customer.
4. If SMTP is not configured in `.env`, the invoice is logged instead of
   emailed, so the project runs without real mail credentials.
