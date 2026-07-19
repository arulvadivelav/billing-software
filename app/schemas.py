from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProductCreate(BaseModel):
    product_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    available_stock: int = Field(..., ge=0)
    price_per_unit: float = Field(..., gt=0)
    tax_percentage: float = Field(0.0, ge=0)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: str
    name: str
    available_stock: int
    price_per_unit: float
    tax_percentage: float


class DenominationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: int
    available_count: int


class BillItemIn(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class DenominationCountIn(BaseModel):
    value: int
    count: int = Field(..., ge=0)


class BillGenerateRequest(BaseModel):
    customer_email: EmailStr
    items: list[BillItemIn]
    denomination_counts: list[DenominationCountIn]
    cash_paid: float = Field(..., ge=0)


class BillItemOut(BaseModel):
    product_id: str
    product_name: str
    unit_price: float
    quantity: int
    purchase_price: float
    tax_percentage: float
    tax_payable: float
    total_price: float


class ChangeDenominationOut(BaseModel):
    value: int
    count: int


class BillResult(BaseModel):
    purchase_id: int
    customer_email: str
    items: list[BillItemOut]
    total_price_without_tax: float
    total_tax_payable: float
    net_price: float
    rounded_net_price: float
    cash_paid: float
    balance_amount: float
    change_denominations: list[ChangeDenominationOut]
    created_at: dt.datetime


class PurchaseSummary(BaseModel):
    id: int
    created_at: dt.datetime
    rounded_net_price: float
    customer_email: str
