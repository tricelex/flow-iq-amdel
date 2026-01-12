"""Custom exceptions for the application."""


class ApplicationException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "", *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


class ValidationError(ApplicationException):
    """Raised when data validation fails."""


class InfrastructureError(ApplicationException):
    """Raised when infrastructure/external service errors occur."""


class DatabaseError(ApplicationException):
    """Raised when database operations fail."""


class ConfigurationError(ApplicationException):
    """Raised when configuration is invalid or missing."""
