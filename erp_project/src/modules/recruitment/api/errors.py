"""
Map recruitment domain exceptions onto HTTP responses.
"""

from rest_framework import status
from rest_framework.response import Response

from shared.domain.exceptions import AuthorizationError, DomainException, NotFoundError


def error_response(exc: DomainException, default_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    if isinstance(exc, AuthorizationError):
        http_status = (
            status.HTTP_401_UNAUTHORIZED
            if exc.code == "UNAUTHENTICATED"
            else status.HTTP_403_FORBIDDEN
        )
        return Response({"error": exc.message, "code": exc.code}, status=http_status)
    if isinstance(exc, NotFoundError):
        return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    # Preserve the views' existing {"error": str(e)} shape for other failures.
    return Response({"error": str(exc)}, status=default_status)
