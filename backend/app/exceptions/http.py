from typing import Any, ClassVar


class AppError(Exception):
    """
    Base for all application-layer exceptions.

    Each subclass declares a status_code class variable.
    handlers.py translates these into JSONResponse objects — business logic
    raises AppError subclasses without knowing anything about HTTP.
    """

    status_code: ClassVar[int] = 500

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code: ClassVar[int] = 404

    def __init__(self, resource: str, identifier: Any = None) -> None:
        detail = (
            f"{resource} with id '{identifier}' not found"
            if identifier is not None
            else f"{resource} not found"
        )
        super().__init__(detail)


class ConflictError(AppError):
    status_code: ClassVar[int] = 409

    def __init__(self, resource: str, field: str, value: str) -> None:
        super().__init__(f"{resource} with {field}='{value}' already exists")


class ValidationError(AppError):
    """
    Business-logic validation failure.

    Distinct from pydantic.ValidationError (request parsing) and
    fastapi.exceptions.RequestValidationError (route parameter validation).
    Use this when a service enforces a rule that Pydantic cannot express,
    e.g. "application status cannot move from REJECTED back to APPLIED".
    """

    status_code: ClassVar[int] = 422

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class UnauthorizedError(AppError):
    status_code: ClassVar[int] = 401

    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(detail)


class ForbiddenError(AppError):
    status_code: ClassVar[int] = 403

    def __init__(
        self, detail: str = "You do not have permission to perform this action"
    ) -> None:
        super().__init__(detail)
