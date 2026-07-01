from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.core.config import API_PREFIX, APP_NAME, APP_VERSION
from app.core.logging_config import logger

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API para monitoreo y visualización de accidentes de tránsito en carreteras del Perú (2020-2021).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(_, exc: ValueError):
    logger.error("ValueError: %s", str(exc))
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get(f"{API_PREFIX}/health")
def health_check():
    return {"status": "ok", "service": "sutran-accidentes-api"}


app.include_router(api_router)
