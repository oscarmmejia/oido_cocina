from .codes import ErrorCode

class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

class TableNotAvailableError(AppError):
    def __init__(self):
        super().__init__(ErrorCode.TABLE_NOT_AVAILABLE,
                         "La mesa no está disponible en esa franja", 409)

class DuplicateReservationError(AppError):
    def __init__(self):
        super().__init__(ErrorCode.DUPLICATE_RESERVATION,
                         "Ya existe una reserva igual", 409)