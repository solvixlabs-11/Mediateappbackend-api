"""Pagination schemas and query parameters."""

from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """Standard pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate SQL offset."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Calculate SQL limit."""
        return self.page_size


class PaginatedResponse[T](BaseModel):
    """Standard paginated list envelope."""

    items: list[T]
    total: int = Field(..., description="Total count matching filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Current page size")
