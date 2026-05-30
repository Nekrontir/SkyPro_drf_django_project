import re
from django.core.exceptions import ValidationError


def validate_youtube_link(value):
    """
    Валидатор: разрешает только ссылки на youtube.com
    """
    if not value:
        return

    if not isinstance(value, str):
        return

    value = value.strip()
    youtube_patterns = [
        r'^https?://(?:www\.)?youtube\.com/.*',
        r'^https?://youtu\.be/.*',
    ]

    is_youtube = any(re.match(pattern, value) for pattern in youtube_patterns)

    if not is_youtube:
        raise ValidationError(
            'Допустимы только ссылки на youtube.com (например, https://www.youtube.com/watch?v=...)',
            params={'value': value},
        )