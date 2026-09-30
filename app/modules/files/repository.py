"""File database repository."""

from sqlalchemy.orm import Session

from app.modules.files.models import FileRecord


class FileRepository:
    """Repository handling file metadata in database."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        filename: str,
        original_filename: str,
        mime_type: str,
        file_size_bytes: int,
        storage_provider: str,
        file_path: str,
        uploaded_by: int | None = None,
    ) -> FileRecord:
        """Create a new FileRecord."""
        record = FileRecord(
            filename=filename,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            storage_provider=storage_provider,
            file_path=file_path,
            uploaded_by=uploaded_by,
            created_by=uploaded_by,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def get_by_id(self, file_id: int) -> FileRecord | None:
        """Retrieve FileRecord by ID."""
        return (
            self.db.query(FileRecord)
            .filter(FileRecord.id == file_id, FileRecord.is_deleted == False)  # noqa: E712
            .first()
        )
