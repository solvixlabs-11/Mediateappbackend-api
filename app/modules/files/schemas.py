"""File schemas for upload and response."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    """File metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    storage_provider: str
    file_url: str
    uploaded_by: int | None = None
    created_at: datetime
