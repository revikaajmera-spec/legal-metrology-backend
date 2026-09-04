from datetime import datetime
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    product_name: str
    brand: str | None = None
    commodity_category: str = Field(examples=["processed", "agricultural", "fast_food"])

    sold_loose: bool = False
    package_intent: str = "retail"
    sale_channel: str = "physical_retail"

    net_quantity: float
    net_quantity_unit: str = Field(examples=["g", "ml", "units"])
    package_area_cm2: float | None = None

    mrp_present: bool = False
    mrp_value: str | None = None
    manufacturer_present: bool = False
    manufacturer_name: str | None = None
    manufacturer_address_present: bool = False
    date_of_manufacture_present: bool = False
    consumer_care_present: bool = False

    declared_font_mm: float | None = None
    contrast_ratio: float | None = None
    calibration_confidence: str = "high"

    state: str | None = None


class ProductOut(ProductCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceResultOut(BaseModel):
    product_id: int
    tier: str
    verdict: str
    exemptions_applied: list[str]
    violations_found: list[str]
    required_font_mm: float | None

    class Config:
        from_attributes = True