"""
ocr_service.py
---------------
This talks to a free cloud OCR service (ocr.space) to "read" text out
of a photo, then does some simple pattern-matching on that text to
guess useful facts about the label -- MRP, net quantity, whether a
manufacturing date is present, etc.

IMPORTANT: this is a light prototype's OCR layer. It is intentionally
simple (regex pattern-matching, not a trained model) -- good enough to
pre-fill a form for a human to review and correct, matching the
proposal's "inspector augmentation, not replacement" design principle.
It should never auto-certify anything on its own.
"""

import re
import requests

from app.config import settings

OCR_SPACE_URL = "https://api.ocr.space/parse/image"


def extract_text_from_image(image_bytes: bytes, filename: str) -> str:
    """
    Sends image bytes to the OCR.space API and returns the raw text
    it found on the image. Raises an exception if the OCR call fails.
    """
    response = requests.post(
        OCR_SPACE_URL,
        files={"file": (filename, image_bytes)},
        data={
            "apikey": settings.ocr_api_key,
            "language": "eng",
            "OCREngine": 2,  # engine 2 is generally better for varied fonts/labels
        },
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("IsErroredOnProcessing"):
        error_message = result.get("ErrorMessage", ["Unknown OCR error"])
        raise RuntimeError(f"OCR failed: {error_message}")

    parsed_results = result.get("ParsedResults") or []
    if not parsed_results:
        return ""

    return parsed_results[0].get("ParsedText", "")


def parse_label_fields(raw_text: str) -> dict:
    """
    Given raw OCR text, look for simple patterns that suggest specific
    Legal Metrology declarations are present. This is heuristic, not
    certain -- the person must still review these before submitting.
    """
    text = raw_text.lower()

    # MRP: look for currency symbol/word followed by digits, e.g. "mrp rs. 199" or "₹199"
    mrp_match = re.search(r"(mrp|rs\.?|₹)\s*[:.]?\s*(\d+(?:\.\d{1,2})?)", text)

    # Net quantity: a number directly followed by g, kg, ml, or l
    qty_match = re.search(r"(\d+(?:\.\d+)?)\s*(g|gm|gms|kg|ml|l|litre|liter)\b", text)

    # Date of manufacture: common abbreviations followed by a date-like pattern
    dom_match = re.search(
        r"(mfd|mfg|manufactured|packed on|pkd)\D{0,10}(\d{1,2}[/-]\d{1,4}|\d{4})",
        text,
    )

    # Consumer care: look for typical customer-care keywords
    care_match = re.search(
        r"(customer care|consumer care|helpline|toll[- ]?free|contact us)", text
    )

        # Manufacturer/address clues: look for common label wording, including
    # abbreviations and punctuation variants seen on real packaging
    # (e.g. "Mfd. by", "Pkd by", "Mfr:", etc.)
    mfr_match = re.search(
        r"(manufactured\s*by|mfd\.?\s*by|mfr\.?\s*by|mfr\.?\s*[:\-]|"
        r"marketed\s*by|packed\s*by|pkd\.?\s*by|\bked\s*by\b)",
        text,
    )
    # Address: state names are a strong signal a full postal address is present,
    # in addition to the word "address" or a 6-digit Indian PIN code
    indian_states = (
        "assam|telangana|maharashtra|gujarat|karnataka|tamil nadu|kerala|"
        "punjab|rajasthan|haryana|bihar|odisha|west bengal|uttar pradesh|"
        "madhya pradesh|andhra pradesh|delhi"
    )
    address_match = re.search(
        rf"(address|{indian_states}|pin\s*[:\-]?\s*\d{{6}}|\b\d{{6}}\b)", text
    )

    return {
        "raw_text": raw_text,
        "mrp_present": bool(mrp_match),
        "mrp_value": mrp_match.group(2) if mrp_match else None,
        "net_quantity": float(qty_match.group(1)) if qty_match else None,
        "net_quantity_unit": _normalize_unit(qty_match.group(2)) if qty_match else None,
        "date_of_manufacture_present": bool(dom_match),
        "consumer_care_present": bool(care_match),
        "manufacturer_present": bool(mfr_match),
        "manufacturer_address_present": bool(address_match),
    }


def _normalize_unit(raw_unit: str) -> str:
    """Maps whatever unit OCR found to the three units our Product model expects."""
    raw_unit = raw_unit.lower()
    if raw_unit in ("g", "gm", "gms", "kg"):
        return "g"
    if raw_unit in ("ml", "l", "litre", "liter"):
        return "ml"
    return "units"