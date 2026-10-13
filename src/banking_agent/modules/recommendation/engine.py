"""Deterministic product selection after Rules grants recommendation permission."""

from collections.abc import Mapping, Sequence

from pydantic import ValidationError

from banking_agent.schemas import (
    ComplaintStatus, ConsentStatus, HandoffStatus, RecommendationItem,
)

from .data import CustomerProfile, DataModel, Product, RecommendationDataset, Text


class RecommendationRequest(DataModel):
    session_id: Text
    complaint_status: ComplaintStatus
    handoff_status: HandoffStatus
    consent: ConsentStatus


def _result(reason_code: str, items: list[RecommendationItem]) -> dict[str, object]:
    return {
        "status": "ok",
        "data": {
            "allowed": bool(items),
            "reason_code": reason_code,
            "items": [item.model_dump(mode="json") for item in items],
        },
    }


def recommend(
    request: Mapping[str, object],
    *,
    customer_profiles: Mapping[str, CustomerProfile | Mapping[str, object]],
    products: Sequence[Product | Mapping[str, object]],
) -> dict[str, object]:
    """Use demo product rules; the caller must first obtain C's RECOMMEND.

    The four-field request cannot prove C permission or expose current risk.
    Defensive checks only reject. Errors use the existing generic envelope.
    """
    try:
        parsed = RecommendationRequest.model_validate(request)
    except ValidationError:
        return {"status": "error", "data": {}}

    if parsed.handoff_status != HandoffStatus.NOT_REQUIRED:
        return {"status": "error", "data": {}}

    if parsed.complaint_status in (ComplaintStatus.OPEN, ComplaintStatus.UNDER_REVIEW):
        return _result("UNRESOLVED_COMPLAINT", [])
    if parsed.consent != ConsentStatus.GRANTED:
        return _result("CONSENT_REQUIRED", [])

    try:
        dataset = RecommendationDataset.model_validate(
            {"customer_profiles": customer_profiles, "products": products}
        )
    except ValidationError:
        return {"status": "error", "data": {}}
    customer = dataset.customer_profiles.get(parsed.session_id)
    if customer is None:
        return {"status": "error", "data": {}}

    eligible = [
        product for product in dataset.products
        if customer.age >= product.min_age
        and customer.residency in product.eligible_residencies
        and customer.available_deposit_cents >= product.min_deposit_cents
    ]
    eligible.sort(key=lambda product: (
        customer.goal not in product.supported_goals,
        product.demo_priority,
        product.product_id,
    ))
    items = [
        RecommendationItem(
            product_id=product.product_id,
            name=product.name,
            rank=rank,
            reason=(
                f"Matches the synthetic '{customer.goal}' goal; satisfies demo "
                "age, residency and deposit conditions."
                if customer.goal in product.supported_goals
                else "Eligible under demo age, residency and deposit conditions; "
                "does not match the requested synthetic goal."
            ),
        )
        for rank, product in enumerate(eligible, start=1)
    ]
    return _result(
        "ELIGIBLE_WITH_CONSENT" if items else "NO_ELIGIBLE_PRODUCT", items
    )
