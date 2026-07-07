"""Custom exceptions for the Verdikta SDK."""


class VerdiktaError(Exception):
    """Base exception for all Verdikta SDK errors."""
    pass


class VerdiktaAPIError(VerdiktaError):
    """Raised when the API returns a non-success status code."""

    def __init__(self, message: str, status_code: int, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"HTTP {status_code}: {message}")


class AuthError(VerdiktaAPIError):
    """Raised on 401/403 responses (invalid or missing API key)."""

    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(message, status_code)


class NotFoundError(VerdiktaAPIError):
    """Raised on 404 responses (job or submission not found)."""

    def __init__(self, message: str = "Resource not found", status_code: int = 404):
        super().__init__(message, status_code)


class RateLimitError(VerdiktaAPIError):
    """Raised on 429 responses."""

    def __init__(self, message: str = "Rate limit exceeded", status_code: int = 429):
        super().__init__(message, status_code)


class ValidationError(VerdiktaAPIError):
    """Raised on 422 responses (invalid request payload)."""

    def __init__(self, message: str = "Validation failed", status_code: int = 422):
        super().__init__(message, status_code)


class NetworkError(VerdiktaError):
    """Raised when a network-level error prevents reaching the API."""
    pass
