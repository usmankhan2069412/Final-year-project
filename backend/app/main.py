import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

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

@app.get("/")
def root():
    return {"message": "Welcome to Aina AI Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
