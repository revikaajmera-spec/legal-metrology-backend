from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.rule_engine import rule_engine

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=schemas.ProductOut)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Save a new product scan to the database."""
    product = models.Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/{product_id}/evaluate", response_model=schemas.ComplianceResultOut)
def evaluate_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = rule_engine.evaluate(product)

    record = models.ComplianceRecord(
        product_id=product.id,
        verdict=result.verdict,
        tier=result.tier,
        exemptions_applied=",".join(result.exemptions_applied) or None,
        violations_found=",".join(result.violations_found) or None,
        required_font_mm=result.required_font_mm,
    )
    db.add(record)
    db.commit()

    return schemas.ComplianceResultOut(
        product_id=product.id,
        tier=result.tier,
        verdict=result.verdict,
        exemptions_applied=result.exemptions_applied,
        violations_found=result.violations_found,
        required_font_mm=result.required_font_mm,
    )