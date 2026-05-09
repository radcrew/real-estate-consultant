"""Human-readable labels for LoopNet-style ``listing_type`` codes."""

from __future__ import annotations

_LISTING_TYPE_LABELS: dict[str, str] = {
    "LandForAuction": "Land for auction",
    "LandForSale": "Land for sale",
    "PropertyForSale": "Property for sale",
    "CommercialPortfolioForAuction": "Commercial portfolio for auction",
    "CommercialPortfolioForSale": "Commercial portfolio for sale",
    "ConsolidatedCondosForSale": "Consolidated condos for sale",
}


def format_listing_type_label(listing_type: str | None) -> str | None:
    """Return a short display label, or ``None`` when ``listing_type`` is empty."""
    if listing_type is None:
        return None
    raw = listing_type.strip()
    if not raw:
        return None
    if raw in _LISTING_TYPE_LABELS:
        return _LISTING_TYPE_LABELS[raw]
    return raw
