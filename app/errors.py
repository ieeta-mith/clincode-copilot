from fastapi import Request
from fastapi.responses import JSONResponse


class ClinCodeError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code


async def clincode_error_handler(request: Request, exc: ClinCodeError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )
