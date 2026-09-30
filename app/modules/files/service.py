"""File management service."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.storage import get_storage_provider
from app.modules.files.models import FileRecord
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import FileResponse

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class FileService:
    """Service orchestrating file validation, storage, and database persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FileRepository(db)
        self.storage = get_storage_provider()
        self.settings = get_settings()

    async def upload_file(
        self,
        file: UploadFile,
        uploaded_by_user_id: int | None = None,
        category: str = "general",
    ) -> FileResponse:
        """Validate and store uploaded file, returning FileResponse with URL."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        mime_type = file.content_type or "application/octet-stream"
        types_str = ", ".join(sorted(ALLOWED_MIME_TYPES))
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{mime_type}'. Allowed types: {types_str}",
            )

        # Read content and validate size
        content = await file.read()
        file_size = len(content)

        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {max_mb}MB",
            )

        # Generate unique storage filename
        extension = Path(file.filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{extension}"
        storage_rel_path = f"{category}/{unique_name}"

        # Persist bytes in StorageProvider
        saved_path = self.storage.save(content, storage_rel_path, mime_type)

        # Persist metadata in database
        record = self.repo.create(
            filename=unique_name,
            original_filename=file.filename,
            mime_type=mime_type,
            file_size_bytes=file_size,
            storage_provider=self.settings.STORAGE_PROVIDER,
            file_path=saved_path,
            uploaded_by=uploaded_by_user_id,
        )
        self.db.commit()
        self.db.refresh(record)

        return self.to_response(record)

    def get_file_content(self, file_id: int) -> tuple[FileRecord, bytes]:
        """Fetch FileRecord and its binary content."""
        record = self.repo.get_by_id(file_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        try:
            content = self.storage.get(record.file_path)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File storage payload missing",
            ) from exc
        return record, content

    def get_file_record(self, file_id: int) -> FileRecord:
        """Fetch FileRecord metadata or raise 404."""
        record = self.repo.get_by_id(file_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        return record

    def to_response(self, record: FileRecord) -> FileResponse:
        """Map FileRecord to FileResponse with reachable URL."""
        file_url = f"{self.settings.API_V1_PREFIX}/files/{record.id}/download"
        return FileResponse(
            id=record.id,
            filename=record.filename,
            original_filename=record.original_filename,
            mime_type=record.mime_type,
            file_size_bytes=record.file_size_bytes,
            storage_provider=record.storage_provider,
            file_url=file_url,
            uploaded_by=record.uploaded_by,
            created_at=record.created_at,
        )
