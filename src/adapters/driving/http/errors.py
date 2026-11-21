from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.errors import (
    DomainError,
    DuplicateStockItemError,
    NotFoundError,
    RecipeGenerationError,
    RecipeGenerationUnavailableError,
    UnknownMemberError,
)

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    UnknownMemberError: status.HTTP_400_BAD_REQUEST,
    DuplicateStockItemError: status.HTTP_409_CONFLICT,
    RecipeGenerationUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    RecipeGenerationError: status.HTTP_502_BAD_GATEWAY,
}


async def _handle_domain_error(_request: Request, error: Exception) -> JSONResponse:
    code = next(
        (status_code for error_type, status_code in _STATUS_BY_ERROR.items() if isinstance(error, error_type)),
        status.HTTP_400_BAD_REQUEST,
    )
    return JSONResponse(status_code=code, content={"detail": str(error)})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
