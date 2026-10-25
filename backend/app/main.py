"""Main FastAPI application entrypoint."""

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes_evaluation import router as evaluation_router
from backend.app.api.routes_ollama import router as ollama_router
from backend.app.api.routes_optimization import router as optimization_router
from backend.app.api.routes_tools import router as tools_router
from backend.app.core.exceptions import AppBaseException
from backend.app.core.logging import logger

app = FastAPI(
    title="Tool Description Optimizer API",
    description="Backend research engine for optimizing agent tool descriptions",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler to prevent stack traces leaking to API responses
@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException):
    logger.error("Handled application exception on %s %s: %s", request.method, request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.message,
        },
    )

# Root service health check
@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

# API v1 router group under /api
api_router = APIRouter(prefix="/api")
api_router.include_router(tools_router)
api_router.include_router(ollama_router)
api_router.include_router(evaluation_router)
api_router.include_router(optimization_router)

app.include_router(api_router)
