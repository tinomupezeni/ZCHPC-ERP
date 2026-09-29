"""
Translate application-layer failures into HTTP responses for payroll views.

The application layer raises ``shared.domain.exceptions`` errors and knows
nothing about HTTP; this is the one place they become status codes.
"""

from rest_framework import status
from rest_framework.response import Response

from shared.domain.exceptions import AuthorizationError, DomainException, NotFoundError


def error_response(exc: DomainException) -> Response:
    if isinstance(exc, AuthorizationError):
        http_status = (
            status.HTTP_401_UNAUTHORIZED
            if exc.code == "UNAUTHENTICATED"
            else status.HTTP_403_FORBIDDEN
        )
    elif isinstance(exc, NotFoundError):
        http_status = status.HTTP_404_NOT_FOUND
    else:
        http_status = status.HTTP_400_BAD_REQUEST
    return Response({"error": exc.message, "code": exc.code}, status=http_status)
