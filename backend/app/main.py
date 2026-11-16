from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db, engine
from app.core.logging_config import setup_logging
from app.core.exceptions import (
    DomainException,
    domain_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.modules.iam.router import router as iam_router
from app.modules.tenancy.router import router as tenancy_router

setup_logging()
logger = logging.getLogger("rcms.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Restaurant & Cafe Management System API...")
    yield
    logger.info("Gracefully shutting down database connections...")
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(iam_router, prefix="/api/v1")
app.include_router(tenancy_router, prefix="/api/v1")


@app.get("/health", tags=["System"], status_code=status.HTTP_200_OK)
def health_check():
    """NFR-026: Liveness check endpoint."""
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/ready", tags=["System"], status_code=status.HTTP_200_OK)
def readiness_check(db: Session = Depends(get_db)):
    """NFR-026: Readiness check verifying PostgreSQL connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
