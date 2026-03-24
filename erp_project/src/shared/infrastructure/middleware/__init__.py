"""
Shared infrastructure middleware.
"""

from shared.infrastructure.middleware.deprecation import DeprecationWarningMiddleware

__all__ = ["DeprecationWarningMiddleware"]
