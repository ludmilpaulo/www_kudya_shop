from pathlib import Path

from django.core.exceptions import ValidationError


ALLOWED_VERIFICATION_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
MAX_VERIFICATION_FILE_SIZE = 10 * 1024 * 1024


def validate_verification_file(file_obj):
    extension = Path(file_obj.name).suffix.lower()
    if extension not in ALLOWED_VERIFICATION_EXTENSIONS:
        raise ValidationError('Unsupported document format. Use PDF, JPG, JPEG, or PNG.')
    if getattr(file_obj, 'size', 0) > MAX_VERIFICATION_FILE_SIZE:
        raise ValidationError('Document exceeds the 10 MB upload limit.')
