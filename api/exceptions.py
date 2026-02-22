"""
Custom exception handler so all API errors return a consistent JSON shape for the frontend.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


def _first_message(detail):
    """Get a single string message from DRF detail (dict, list, or string)."""
    if isinstance(detail, dict):
        first_key = next(iter(detail))
        val = detail[first_key]
        if isinstance(val, list):
            return val[0] if val else str(val)
        return str(val)
    if isinstance(detail, list):
        return detail[0] if detail else "Validation error"
    return str(detail)


def _normalize_details(detail):
    """Turn DRF detail into a flat dict of field -> message for 'details'."""
    if isinstance(detail, dict):
        out = {}
        for k, v in detail.items():
            if isinstance(v, list):
                out[k] = v[0] if v else str(v)
            else:
                out[k] = str(v)
        return out
    if isinstance(detail, list) and detail:
        return {"detail": _first_message(detail)}
    return {"detail": str(detail)}


def api_exception_handler(exc, context):
    """
    Format all API errors as: { "error": true, "message": "...", "details": { ... } }.
    """
    response = exception_handler(exc, context)
    if response is None:
        # Unhandled exception (e.g. 500) – always return JSON, never HTML
        payload = {
            "error": True,
            "message": "An unexpected error occurred.",
            "details": {},
        }
        if settings.DEBUG:
            payload["details"]["debug"] = str(exc)
        return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    detail = getattr(exc, "detail", response.data)
    message = _first_message(detail)
    details = _normalize_details(detail)

    response.data = {
        "error": True,
        "message": message,
        "details": details,
    }
    return response
