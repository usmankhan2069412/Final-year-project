import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.bots import router as bots_router
from app.api.v1.models import router as models_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.messaging import router as messaging_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

# 🗄️ Auto-create database tables on startup if they don't exist
from app.db.session import engine
from app.db.base import Base
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
except Exception as e:
    logger.error("Could not automatically create/verify database tables on boot: %s", str(e))

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 🌐 CORS Middleware Configuration
# Allows the React/Vite frontend (running on other localhost ports) to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ Global Database Exception Handler
# Prevents backend from crashing on db connection failures and keeps details out of the API response
@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    # Log the real error securely on the server side so developers can diagnose it
    logger.error("Database connection or query execution failure: %s", str(exc), exc_info=True)
    
    # Return a clean, safe, and structured 503 response to the frontend client
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database service is temporarily unavailable. Please verify that the database server is running and connection credentials in your .env file are correct."
        }
    )

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(bots_router, prefix=f"{settings.API_V1_STR}", tags=["bots"])
app.include_router(models_router, prefix=f"{settings.API_V1_STR}/models", tags=["models"])
app.include_router(knowledge_router, prefix=f"{settings.API_V1_STR}/knowledge", tags=["knowledge"])
app.include_router(messaging_router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])

from app.api.v1.analytics import router as analytics_router
from app.api.v1.agents import router as agents_router

app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(agents_router, prefix=f"{settings.API_V1_STR}/agents", tags=["agents"])

from app.api.v1.channels import router as channels_router
from app.api.v1.deployments import router as deployments_router
from app.api.v1.billing import router as billing_router
from app.api.v1.team import router as team_router
from app.api.v1.api_keys import router as api_keys_router

app.include_router(channels_router, prefix=f"{settings.API_V1_STR}/channels", tags=["channels"])
app.include_router(deployments_router, prefix=f"{settings.API_V1_STR}/deployments", tags=["deployments"])
app.include_router(billing_router, prefix=f"{settings.API_V1_STR}")
app.include_router(team_router, prefix=f"{settings.API_V1_STR}")
app.include_router(api_keys_router, prefix=f"{settings.API_V1_STR}")

from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.analytics_aggregation import run_nightly_aggregation

@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run daily aggregation at 12:05 AM (00:05) every day
    scheduler.add_job(run_nightly_aggregation, "cron", hour=0, minute=5)
    scheduler.start()
    logger.info("APScheduler initialized and started nightly aggregation task.")


@app.get("/")
def root():
    return {"message": "Welcome to Aina AI Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
