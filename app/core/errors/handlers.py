import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .codes import ErrorCode
from .exceptions import AppError
from .schemas import ErrorBody, ErrorResponse

logger = logging.getLogger(__name__)

HTTP_DEFAULTS = {
    400: (ErrorCode.BAD_REQUEST, "Solicitud incorrecta"),
    401: (ErrorCode.UNAUTHORIZED, "No autenticado"),
    403: (ErrorCode.FORBIDDEN, "No tienes permisos"),
    404: (ErrorCode.NOT_FOUND, "Recurso no encontrado"),
    409: (ErrorCode.CONFLICT, "Conflicto con el estado actual"),
}

def _response(status: int, code: ErrorCode, message: str) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code.value, message=message))
    return JSONResponse(status_code=status, content=body.model_dump())

async def app_error_handler(request: Request, exc: AppError):
    return _response(exc.status_code, exc.code, exc.message)

async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code, msg = HTTP_DEFAULTS.get(exc.status_code, (ErrorCode.BAD_REQUEST, "Solicitud incorrecta"))
    return _response(exc.status_code, code, msg)

async def validation_error_handler(request: Request, exc: RequestValidationError):
    return _response(422, ErrorCode.VALIDATION_ERROR, "Los datos enviados no son válidos")

async def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("Error no controlado")
    return _response(500, ErrorCode.INTERNAL_ERROR, "Error interno del servidor")

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)