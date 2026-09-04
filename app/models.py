"""
models.py
---------
These classes describe the SHAPE of our database tables.
Each class = one table. Each attribute = one column.
SQLAlchemy turns these Python classes into real database tables for us.
"""

from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    """
    One row = one product scan submitted for checking.
    This holds the RAW facts about the package -- the same fields
    our rule engine needs to decide compliance.
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    product_name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(255), nullable=True)
    commodity_category: Mapped[str] = mapped_column(String(100))  # e.g. "processed", "unprocessed_agricultural"

    sold_loose: Mapped[bool] = mapped_column(Boolean, default=False)
    package_intent: Mapped[str] = mapped_column(String(50), default="retail")  # "retail" or "wholesale_not_retail"
    sale_channel: Mapped[str] = mapped_column(String(50), default="physical_retail")

    net_quantity: Mapped[float] = mapped_column(Float)
    net_quantity_unit: Mapped[str] = mapped_column(String(10))  # "g", "ml", "units"
    package_area_cm2: Mapped[float] = mapped_column(Float, nullable=True)

    # Declared label facts (what the label actually shows, to be checked)
    mrp_present: Mapped[bool] = mapped_column(Boolean, default=False)
    mrp_value: Mapped[str] = mapped_column(String(50), nullable=True)
    manufacturer_present: Mapped[bool] = mapped_column(Boolean, default=False)
    manufacturer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    manufacturer_address_present: Mapped[bool] = mapped_column(Boolean, default=False)
    date_of_manufacture_present: Mapped[bool] = mapped_column(Boolean, default=False)
    consumer_care_present: Mapped[bool] = mapped_column(Boolean, default=False)

    declared_font_mm: Mapped[float] = mapped_column(Float, nullable=True)
    contrast_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    calibration_confidence: Mapped[str] = mapped_column(String(20), default="high")  # "high"/"medium"/"low"

    state: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # One product can have many compliance check runs over time
    compliance_records: Mapped[list["ComplianceRecord"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ComplianceRecord(Base):
    """
    One row = one result of running the rule engine against a Product.
    We keep every past run so nothing is silently overwritten --
    this matches the proposal's audit-trail requirement (Section 4).
    """
    __tablename__ = "compliance_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))

    verdict: Mapped[str] = mapped_column(String(50))          # e.g. "Certified_Violation"
    tier: Mapped[str] = mapped_column(String(20))              # "Advisory" or "Certified"
    exemptions_applied: Mapped[str] = mapped_column(Text, nullable=True)   # comma-separated ids
    violations_found: Mapped[str] = mapped_column(Text, nullable=True)     # comma-separated ids
    required_font_mm: Mapped[float] = mapped_column(Float, nullable=True)

    officer_rationale: Mapped[str] = mapped_column(Text, nullable=True)   # required for Certified tier
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="compliance_records")