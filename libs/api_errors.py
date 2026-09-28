"""Stable error response format shared by all API applications."""

from rest_framework.views import exception_handler as drf_exception_handler


MESSAGE_KEYS = (
    ("already registered", "EMAIL_ALREADY_USED"),
    ("déjà associée à un compte", "EMAIL_ALREADY_USED"),
    ("email déjà", "EMAIL_ALREADY_USED"),
    ("email already verified", "EMAIL_ALREADY_VERIFIED"),
    ("email already", "EMAIL_ALREADY_VERIFIED"),
    ("no email associated", "EMAIL_NOT_ASSOCIATED"),
    ("no email", "EMAIL_NOT_ASSOCIATED"),
    ("user has already a company", "COMPANY_ALREADY_EXISTS"),
    ("confirm required", "CONFIRMATION_REQUIRED"),
    ("raison est obligatoire", "REJECTION_REASON_REQUIRED"),
    ("temporarily locked", "ACCOUNT_LOCKED"),
    ("username", "USERNAME_ALREADY_USED"),
    ("nom d'utilisateur est déjà", "USERNAME_ALREADY_USED"),
    ("password", "INVALID_CREDENTIALS"),
    ("mot de passe", "INVALID_CREDENTIALS"),
    ("verification code", "INVALID_OR_EXPIRED_CODE"),
    ("verification", "INVALID_OR_EXPIRED_CODE"),
    ("code", "INVALID_OR_EXPIRED_CODE"),
    ("company not found", "COMPANY_NOT_FOUND"),
    ("company not", "COMPANY_NOT_FOUND"),
    ("self", "ACTION_NOT_ALLOWED"),
    ("vous ne pouvez pas", "ACTION_NOT_ALLOWED"),
    ("not found", "RESOURCE_NOT_FOUND"),
    ("introuvable", "RESOURCE_NOT_FOUND"),
    ("déjà en cours", "VERIFICATION_ALREADY_PENDING"),
    ("already being processed", "VERIFICATION_ALREADY_PENDING"),
    ("déjà vérifiée", "IDENTITY_ALREADY_VERIFIED"),
)


def _strings(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _strings(child)
    else:
        yield str(value)


def _error_key(data, status_code):
    if isinstance(data, dict) and data.get("code"):
        return data["code"]

    searchable = " ".join(_strings(data)).lower()
    for fragment, key in MESSAGE_KEYS:
        if fragment in searchable:
            return key

    if status_code == 400:
        return "VALIDATION_ERROR"
    if status_code == 401:
        return "AUTHENTICATION_REQUIRED"
    if status_code == 403:
        return "PERMISSION_DENIED"
    if status_code == 404:
        return "RESOURCE_NOT_FOUND"
    if status_code == 409:
        return "RESOURCE_CONFLICT"
    if status_code == 429:
        return "TOO_MANY_REQUESTS"
    if status_code >= 500:
        return "INTERNAL_SERVER_ERROR"
    return "REQUEST_ERROR"


def error_payload(data, status_code):
    if isinstance(data, dict):
        detail = next(
            (data[field] for field in ("detail", "error", "message") if field in data),
            data,
        )
        metadata = {
            key: value
            for key, value in data.items()
            if key not in {"key", "code", "detail", "error", "message"}
        }
        if metadata:
            detail = {"message": detail, **metadata}
    else:
        detail = data
    return {"code": _error_key(data, status_code), "detail": detail}


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = error_payload(response.data, response.status_code)
    return response


class ErrorResponseMiddleware:
    """Normalizes errors returned directly by views as well as DRF exceptions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_template_response(self, request, response):
        if response.status_code >= 400 and hasattr(response, "data"):
            response.data = error_payload(response.data, response.status_code)
        return response
