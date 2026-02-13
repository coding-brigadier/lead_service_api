import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _validate_file(file: UploadFile) -> str:
    """Validate the uploaded file's extension and return it."""
    if file.filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    return ext


async def save_resume(file: UploadFile) -> str:
    """Validate and save an uploaded resume file. Returns the storage path."""
    ext = _validate_file(file)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 10 MB).")

    unique_name = f"{uuid.uuid4().hex}{ext}"

    if settings.STORAGE_BACKEND == "s3":
        return await _save_to_s3(unique_name, contents)
    return _save_to_local(unique_name, contents)


def _save_to_local(filename: str, contents: bytes) -> str:
    """Write file contents to the local uploads directory."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(contents)
    return path


async def _save_to_s3(filename: str, contents: bytes) -> str:
    """Upload file contents to S3 and return the s3:// URI."""
    import aiobotocore.session

    key = f"{settings.S3_PREFIX}{filename}"
    session = aiobotocore.session.get_session()
    kwargs = {"region_name": settings.S3_REGION}
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    async with session.create_client("s3", **kwargs) as client:
        await client.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=contents)
    return f"s3://{settings.S3_BUCKET}/{key}"
