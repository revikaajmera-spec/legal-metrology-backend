"""
rule_engine.py
--------------
This is the "brain" of the compliance checker.

It takes ONE product's facts (from the database) and returns a decision:
  - which exemptions apply (if any)
  - which mandatory declarations are missing
  - whether the required font size was met
  - a final verdict: Certified_Compliant / Certified_Violation / Advisory

IMPORTANT DESIGN RULE (straight from the proposal, Section 6):
  Exemptions are checked FIRST. If a product is exempt, we do NOT run
  the mandatory-declaration or font checks at all -- an exempt product
  cannot be "in violation".
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field

from app.config import settings
from app.models import Product


@dataclass
class ComplianceResult:
    tier: str                      # "Advisory" or "Certified"
    verdict: str                   # human-readable final verdict
    exemptions_applied: list = field(default_factory=list)
    violations_found: list = field(default_factory=list)
    required_font_mm: float | None = None


class RuleEngine:
    def __init__(self, rules_path: str | None = None):
        path = Path(rules_path or settings.rules_file_path)
        with open(path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)

    # -----------------------------------------------------------------
    # STEP 1: Exemptions (Rule 26 + Rule 3 scope) -- checked first
    # -----------------------------------------------------------------
    def _check_exemptions(self, product: Product) -> list[str]:
        applied = []

        # EXM-R26a-small-pack: net qty <= 10, unit is g or ml
        if product.net_quantity_unit in ("g", "ml") and product.net_quantity <= 10:
            applied.append("EXM-R26a-small-pack")

        # EXM-R3-loose-goods
        if product.sold_loose:
            applied.append("EXM-R3-loose-goods")

        # EXM-R26d-agri-produce: agricultural category AND qty > 50kg (50000g)
        if product.commodity_category == "agricultural" and product.net_quantity_unit == "g" \
                and product.net_quantity > 50000:
            applied.append("EXM-R26d-agri-produce")

        # EXM-R26b-fast-food
        if product.commodity_category == "fast_food":
            applied.append("EXM-R26b-fast-food")

        return applied

    # -----------------------------------------------------------------
    # STEP 2: Required font height, from Rule 7 Table I (by net quantity)
    # -----------------------------------------------------------------
    def _required_font_mm(self, product: Product) -> float | None:
        if product.net_quantity_unit not in ("g", "ml"):
            return None  # Table II (by area) not wired up in this light prototype

        for tier in self.rules["font_height_by_quantity"]:
            if tier["max_qty_g_or_ml"] is None or product.net_quantity <= tier["max_qty_g_or_ml"]:
                return tier["min_height_mm_normal"]
        return None

    # -----------------------------------------------------------------
    # STEP 3: Mandatory declarations (Rule 6), only runs if NOT exempt
    # -----------------------------------------------------------------
    def _check_mandatory_declarations(self, product: Product) -> list[str]:
        violations = []
        for decl in self.rules["mandatory_declarations"]:
            field_value = getattr(product, decl["field"], None)
            if not field_value:
                violations.append(decl["id"])
        return violations

    def _check_font_height(self, product: Product, required_mm: float | None) -> bool:
        """Returns True if there IS a font violation."""
        if required_mm is None or product.declared_font_mm is None:
            return False
        return product.declared_font_mm < required_mm

    # -----------------------------------------------------------------
    # MAIN ENTRY POINT
    # -----------------------------------------------------------------
    def evaluate(self, product: Product) -> ComplianceResult:
        exemptions = self._check_exemptions(product)

        if exemptions:
            return ComplianceResult(
                tier="Certified",
                verdict="Certified_Compliant (exempt)",
                exemptions_applied=exemptions,
            )

        required_font = self._required_font_mm(product)
        violations = self._check_mandatory_declarations(product)

        if self._check_font_height(product, required_font):
            violations.append("LM-R8-font-height")

        # Low calibration confidence -> can never be Certified, only Advisory
        # (mirrors the proposal's "tamper-evidence, not tamper-proof" design)
        if product.calibration_confidence == "low":
            return ComplianceResult(
                tier="Advisory",
                verdict="Advisory (low calibration confidence - not certifiable)",
                exemptions_applied=[],
                violations_found=violations,
                required_font_mm=required_font,
            )

        if violations:
            verdict = "Certified_Violation"
        else:
            verdict = "Certified_Compliant"

        return ComplianceResult(
            tier="Certified",
            verdict=verdict,
            exemptions_applied=[],
            violations_found=violations,
            required_font_mm=required_font,
        )


# One shared instance the rest of the app can import and reuse.
rule_engine = RuleEngine()