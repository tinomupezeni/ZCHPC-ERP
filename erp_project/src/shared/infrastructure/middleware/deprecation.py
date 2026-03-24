"""
Deprecation warning middleware.

Adds deprecation headers to responses from legacy API endpoints,
informing clients to migrate to the new v2 API.
"""

import warnings
from typing import Callable

from django.http import HttpRequest, HttpResponse


class DeprecationWarningMiddleware:
    """
    Middleware that adds deprecation warning headers to legacy API endpoints.

    This middleware checks if the request path matches any deprecated API paths
    and adds appropriate headers to inform clients about the deprecation.
    """

    # Map of deprecated paths to their new v2 equivalents
    DEPRECATED_PATHS = {
        "/api/hr/": {
            "replacement": "/api/v2/hr/",
            "sunset": "2026-06-01",
            "message": "The /api/hr/ endpoint is deprecated. Please migrate to /api/v2/hr/",
        },
        "/api/auth/": {
            "replacement": "/api/v2/auth/",
            "sunset": "2026-06-01",
            "message": "The /api/auth/ endpoint is deprecated. Please migrate to /api/v2/auth/",
        },
        "/api/portal/attendance/": {
            "replacement": "/api/v2/attendance/",
            "sunset": "2026-06-01",
            "message": "The /api/portal/attendance/ endpoint is deprecated. Please migrate to /api/v2/attendance/",
        },
        "/api/hr/attendance/": {
            "replacement": "/api/v2/attendance/",
            "sunset": "2026-06-01",
            "message": "The /api/hr/attendance/ endpoint is deprecated. Please migrate to /api/v2/attendance/",
        },
    }

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and add deprecation headers if needed."""
        response = self.get_response(request)

        # Check if the request path matches any deprecated paths
        for deprecated_path, info in self.DEPRECATED_PATHS.items():
            if request.path.startswith(deprecated_path):
                # Add deprecation warning headers
                response["Deprecation"] = "true"
                response["Sunset"] = info["sunset"]
                response["Link"] = f'<{info["replacement"]}>; rel="successor-version"'
                response["X-Deprecation-Notice"] = info["message"]

                # Log a warning for server-side monitoring
                warnings.warn(
                    f"Deprecated API endpoint accessed: {request.path}. "
                    f"Recommend using: {info['replacement']}",
                    DeprecationWarning,
                    stacklevel=2,
                )
                break

        return response
