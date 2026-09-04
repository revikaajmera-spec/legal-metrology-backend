"""
routers/ocr.py
---------------
One door: POST /ocr/scan-label

Accepts an uploaded image, sends it through the OCR service, and
returns both the raw text found and our best-guess field extraction --
the frontend will pre-fill the product form with these guesses, but
the person still reviews and corrects them before submitting.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.ocr_service import extract_text_from_image, parse_label_fields

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/scan-label")
async def scan_label(file: UploadFile = File(...)):
    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        raw_text = extract_text_from_image(image_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be read from this image. Try a clearer photo.",
        )

    extracted = parse_label_fields(raw_text)
    return extracted