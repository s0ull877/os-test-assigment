from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.app.core.services import ServiceError
from src.app.infrastructure.config import get_settings

from .routers import router as booking_router

app_settings = get_settings()

app = FastAPI(
    title=app_settings.app_name,
    debug=app_settings.debug,
)


@app.exception_handler(ServiceError)
async def service_error_handler(
    exc: ServiceError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


app.include_router(router=booking_router)
