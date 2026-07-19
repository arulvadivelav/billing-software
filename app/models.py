from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    available_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    tax_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    purchase_items: Mapped[list["PurchaseItem"]] = relationship(back_populates="product")


class Denomination(Base):
    __tablename__ = "denominations"
    __table_args__ = (UniqueConstraint("value", name="uq_denomination_value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    available_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    total_price_without_tax: Mapped[float] = mapped_column(Float, nullable=False)
    total_tax_payable: Mapped[float] = mapped_column(Float, nullable=False)
    net_price: Mapped[float] = mapped_column(Float, nullable=False)
    rounded_net_price: Mapped[float] = mapped_column(Float, nullable=False)
    cash_paid: Mapped[float] = mapped_column(Float, nullable=False)
    balance_amount: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )

    items: Mapped[list["PurchaseItem"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )
    change_given: Mapped[list["PurchaseChangeGiven"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    product_business_id: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    tax_percentage: Mapped[float] = mapped_column(Float, nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    tax_payable: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    purchase: Mapped["Purchase"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="purchase_items")


class PurchaseChangeGiven(Base):
    __tablename__ = "purchase_change_given"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id"), nullable=False)
    denomination_value: Mapped[int] = mapped_column(Integer, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)

    purchase: Mapped["Purchase"] = relationship(back_populates="change_given")
