from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible


MB = 1024 * 1024

IMAGE_MAX_SIZE = 5 * MB
PDF_MAX_SIZE = 25 * MB
VIDEO_MAX_SIZE = 500 * MB

IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "webp", "gif")
PDF_EXTENSIONS = ("pdf",)
VIDEO_EXTENSIONS = ("mp4", "mov", "webm")

IMAGE_CONTENT_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif")
PDF_CONTENT_TYPES = ("application/pdf",)
VIDEO_CONTENT_TYPES = ("video/mp4", "video/quicktime", "video/webm")


def format_file_size(size):
    if size % MB == 0:
        return f"{size // MB} MB"
    return f"{size} bytes"


@deconstructible
class FileSizeValidator:
    def __init__(self, max_size):
        self.max_size = max_size

    def __call__(self, value):
        size = getattr(value, "size", None)
        if size is not None and size > self.max_size:
            raise ValidationError(
                f"File size must not exceed {format_file_size(self.max_size)}."
            )

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.max_size == other.max_size


@deconstructible
class FileContentTypeValidator:
    def __init__(self, allowed_content_types):
        self.allowed_content_types = tuple(allowed_content_types)

    def __call__(self, value):
        content_type = getattr(value, "content_type", None)
        if content_type and content_type not in self.allowed_content_types:
            allowed = ", ".join(self.allowed_content_types)
            raise ValidationError(f"Unsupported file content type. Allowed: {allowed}.")

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.allowed_content_types == other.allowed_content_types
        )


@deconstructible
class FileSignatureValidator:
    def __init__(self, signature, message):
        self.signature = signature
        self.message = message

    def __call__(self, value):
        if not hasattr(value, "read"):
            return

        position = None
        if hasattr(value, "tell"):
            try:
                position = value.tell()
            except (OSError, ValueError):
                position = None

        header = value.read(len(self.signature))

        if position is not None and hasattr(value, "seek"):
            try:
                value.seek(position)
            except (OSError, ValueError):
                pass

        if header != self.signature:
            raise ValidationError(self.message)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.signature == other.signature
            and self.message == other.message
        )


image_file_validators = [
    FileExtensionValidator(IMAGE_EXTENSIONS),
    FileContentTypeValidator(IMAGE_CONTENT_TYPES),
    FileSizeValidator(IMAGE_MAX_SIZE),
]

pdf_file_validators = [
    FileExtensionValidator(PDF_EXTENSIONS),
    FileContentTypeValidator(PDF_CONTENT_TYPES),
    FileSizeValidator(PDF_MAX_SIZE),
    FileSignatureValidator(b"%PDF", "Uploaded file must be a valid PDF document."),
]

video_file_validators = [
    FileExtensionValidator(VIDEO_EXTENSIONS),
    FileContentTypeValidator(VIDEO_CONTENT_TYPES),
    FileSizeValidator(VIDEO_MAX_SIZE),
]
