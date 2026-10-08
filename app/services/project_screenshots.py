"""Validation and filesystem operations for project screenshots."""

from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError


SCREENSHOTS_UPLOAD_DIR = Path("app/static/uploads/project_screenshots")
PUBLIC_SCREENSHOTS_PREFIX = "/static/uploads/project_screenshots/"
SUPPORTED_IMAGE_FORMATS = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
}


class InvalidScreenshotError(ValueError):
    """Raised when an uploaded file is not a supported, valid image."""


def validate_screenshot(upload: UploadFile) -> str:
    """Validate image content and return a safe extension derived from it."""

    try:
        upload.file.seek(0)
        with Image.open(upload.file) as image:
            image_format = image.format
            image.verify()
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise InvalidScreenshotError(
            f"Файл «{upload.filename or 'без имени'}» не является поддерживаемым изображением."
        ) from exc
    finally:
        upload.file.seek(0)

    extension = SUPPORTED_IMAGE_FORMATS.get(image_format or "")
    if extension is None:
        raise InvalidScreenshotError(
            f"Файл «{upload.filename or 'без имени'}» имеет неподдерживаемый формат. "
            "Разрешены PNG, JPEG и WebP."
        )

    return extension


def store_screenshot(upload: UploadFile, extension: str) -> str:
    """Stream an already validated upload to a UUID-named persistent file."""

    SCREENSHOTS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"screenshot_{uuid4().hex}{extension}"
    destination = SCREENSHOTS_UPLOAD_DIR / filename

    upload.file.seek(0)
    with destination.open("wb") as output:
        copyfileobj(upload.file, output)

    return f"{PUBLIC_SCREENSHOTS_PREFIX}{filename}"


def delete_screenshot_file(image_path: str) -> None:
    """Delete only a file that belongs to the screenshots upload directory."""

    if not image_path.startswith(PUBLIC_SCREENSHOTS_PREFIX):
        return

    filename = image_path.removeprefix(PUBLIC_SCREENSHOTS_PREFIX)
    if not filename or Path(filename).name != filename:
        return

    file_path = SCREENSHOTS_UPLOAD_DIR / filename
    try:
        file_path.unlink()
    except FileNotFoundError:
        pass
