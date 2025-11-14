"""
Custom exceptions for Claudia backend

Provides domain-specific exceptions for better error handling and
structured HTTP error responses.
"""
from fastapi import HTTPException, status


class ClaudiaException(Exception):
    """Base exception for Claudia-specific errors"""
    pass


class SessionNotFoundException(ClaudiaException):
    """Raised when a session cannot be found in the database"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class ServiceNotInitializedException(ClaudiaException):
    """Raised when a required service is not initialized"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Service not initialized: {service_name}")


class DirectoryNotFoundException(ClaudiaException):
    """Raised when a required directory does not exist"""

    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        super().__init__(f"Required directory not found: {directory_path}")


def session_not_found_error(session_id: str) -> HTTPException:
    """
    Convert SessionNotFoundException to HTTP 422 Unprocessable Entity

    Returns structured error response with session_id for debugging
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "session_not_found",
            "message": f"Session '{session_id}' does not exist. Session may not have been created or has been removed.",
            "session_id": session_id
        }
    )


def service_not_initialized_error(service_name: str) -> HTTPException:
    """
    Convert ServiceNotInitializedException to HTTP 503 Service Unavailable

    Returns structured error response indicating which service is unavailable
    """
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "service_unavailable",
            "message": f"Required service '{service_name}' is not initialized",
            "service": service_name
        }
    )
