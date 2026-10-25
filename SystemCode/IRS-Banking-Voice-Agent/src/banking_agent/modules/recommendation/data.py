"""Module-local synthetic data models; shared State stays unchanged."""

from pathlib import Path
from typing import Annotated, Self

from pydantic import (
    AfterValidator, BaseModel, ConfigDict, Field, StrictBool, model_validator,
)


def _nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("Text must not be blank")
    return value


Text = Annotated[str, Field(strict=True, min_length=1), AfterValidator(_nonblank)]
NonnegativeInt = Annotated[int, Field(strict=True, ge=0)]
Conditions = Annotated[tuple[Text, ...], Field(min_length=1)]


class DataModel(BaseModel):
    """Reject unknown fields and implicit numeric conversions."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class CustomerProfile(DataModel):
    customer_id: Text
    age: NonnegativeInt
    residency: Text
    available_deposit_cents: NonnegativeInt
    goal: Text


class Product(DataModel):
    product_id: Text
    name: Text
    min_age: NonnegativeInt
    eligible_residencies: Conditions
    min_deposit_cents: NonnegativeInt
    supported_goals: Conditions
    demo_priority: NonnegativeInt


class RecommendationDataset(DataModel):
    customer_profiles: dict[Text, CustomerProfile]
    products: tuple[Product, ...]

    @model_validator(mode="after")
    def unique_product_ids(self) -> Self:
        ids = [product.product_id for product in self.products]
        if len(ids) != len(set(ids)):
            raise ValueError("Product IDs must be unique")
        return self


class SyntheticFixture(RecommendationDataset):
    synthetic: StrictBool

    @model_validator(mode="after")
    def require_synthetic_data(self) -> Self:
        if self.synthetic is not True:
            raise ValueError("Fixtures must be explicitly synthetic")
        return self


def load_fixture(path: str | Path) -> SyntheticFixture:
    """Load an explicit trusted path once; I/O errors propagate to the caller."""
    return SyntheticFixture.model_validate_json(
        Path(path).read_text(encoding="utf-8")
    )
