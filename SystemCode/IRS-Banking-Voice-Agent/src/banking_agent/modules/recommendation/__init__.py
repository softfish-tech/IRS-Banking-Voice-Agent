"""Eligibility-aware, synthetic recommendation reference implementation."""
from .adapter import RecommendationAdapter
from .data import CustomerProfile, Product, RecommendationDataset, SyntheticFixture, load_fixture
from .engine import recommend

__all__ = [
    "CustomerProfile", "Product", "RecommendationDataset", "SyntheticFixture",
    "load_fixture", "recommend", "RecommendationAdapter",
]
