import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.exceptions.handlers import register_exception_handlers
from app.features.applications.router import router as applications_router
from app.features.companies.router import router as companies_router
from app.features.cover_letter_ai.router import router as cover_letter_ai_router
from app.features.cover_letters.router import router as cover_letters_router
from app.features.followups.router import router as followups_router
from app.features.gmail.router import router as gmail_router
from app.features.interviews.router import router as interviews_router
from app.features.recruiters.router import router as recruiters_router
from app.features.resume_match.router import router as resume_match_router
from app.features.resumes.router import router as resumes_router

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting ApplyTrack API | environment=%s", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down ApplyTrack API")


app = FastAPI(
    title="ApplyTrack API",
    version="0.1.0",
    lifespan=lifespan,
    # Swagger UI and OpenAPI schema are disabled in production to reduce
    # the exposed attack surface. Enable them only for development/staging.
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(companies_router, prefix=settings.API_V1_PREFIX)
app.include_router(applications_router, prefix=settings.API_V1_PREFIX)
app.include_router(recruiters_router, prefix=settings.API_V1_PREFIX)
app.include_router(interviews_router, prefix=settings.API_V1_PREFIX)
app.include_router(followups_router, prefix=settings.API_V1_PREFIX)
app.include_router(gmail_router, prefix=settings.API_V1_PREFIX)
app.include_router(resumes_router, prefix=settings.API_V1_PREFIX)
app.include_router(cover_letters_router, prefix=settings.API_V1_PREFIX)
app.include_router(resume_match_router, prefix=settings.API_V1_PREFIX)
app.include_router(cover_letter_ai_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["infrastructure"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
