"""Async D boundary matching E's public RecommendationModule Protocol."""
from collections.abc import Mapping

from .data import RecommendationDataset, SyntheticFixture
from .engine import recommend


class RecommendationAdapter:
    """Snapshot explicitly injected demo data; never select a default customer.

    E must first obtain C's RECOMMEND. This adapter has no network or file I/O,
    and the session/profile mapping is synthetic configuration, not authentication.
    """

    def __init__(self, dataset: RecommendationDataset | Mapping[str, object]) -> None:
        if isinstance(dataset, SyntheticFixture):
            fixture = SyntheticFixture.model_validate(dataset)
            dataset = {"customer_profiles": fixture.customer_profiles, "products": fixture.products}
        self._dataset = RecommendationDataset.model_validate(dataset).model_copy(deep=True)

    async def recommend(
        self, session_id: str, complaint_status: str, handoff_status: str, consent: str,
    ) -> dict[str, object]:
        result = recommend(
            {"session_id": session_id, "complaint_status": complaint_status,
             "handoff_status": handoff_status, "consent": consent},
            customer_profiles=self._dataset.customer_profiles,
            products=self._dataset.products,
        )
        # E's ModuleResult[RecommendationData] rejects data={} even on errors.
        # Omitting data is supported by E and preserves the technical-error status.
        return {"status": "error"} if result["status"] == "error" else result
