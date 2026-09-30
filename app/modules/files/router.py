"""Files HTTP endpoints."""

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.files.schemas import FileResponse
from app.modules.files.service import FileService
from app.modules.users.models import User

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file or image",
)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Upload a file (photo, document) through StorageProvider."""
    service = FileService(db)
    return await service.upload_file(file, uploaded_by_user_id=current_user.id)


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file metadata",
)
def get_file_metadata(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Get metadata for an existing file record."""
    service = FileService(db)
    record = service.get_file_record(file_id)
    return service.to_response(record)


@router.get(
    "/{file_id}/download",
    summary="Download or stream file content",
)
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Serve binary file bytes."""
    service = FileService(db)
    record, content = service.get_file_content(file_id)
    return Response(
        content=content,
        media_type=record.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{record.original_filename}"',
        },
    )
