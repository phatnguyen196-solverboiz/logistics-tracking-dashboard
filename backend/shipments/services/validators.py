import re

from django.core.exceptions import ValidationError


TRACKING_NUMBER_PATTERN = re.compile(r"^[A-Z0-9-]{6,40}$")


def normalize_tracking_number(value: str) -> str:
    normalized = value.strip().upper()
    if not TRACKING_NUMBER_PATTERN.fullmatch(normalized):
        raise ValidationError("Use 6-40 uppercase letters, numbers, or hyphens.")
    return normalized
