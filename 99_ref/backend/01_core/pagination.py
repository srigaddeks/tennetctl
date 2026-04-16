from __future__ import annotations

from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    model_config = {"frozen": True}

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response envelope."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginationParams:
    """FastAPI dependency for extracting pagination query params."""
    return PaginationParams(page=page, page_size=page_size)


def paginate(items: list[T], *, total: int, params: PaginationParams) -> PaginatedResponse[T]:
    """Build a PaginatedResponse from a list of items and total count."""
    total_pages = ceil(total / params.page_size) if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
    )
