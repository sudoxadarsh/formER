from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import client
from .routers import auth_routes, profile_routes, history_routes, issue_routes, stats_routes, ml_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify MongoDB connection on startup
    try:
        await client.admin.command("ping")
        print(f"Connected to MongoDB successfully ({settings.MONGODB_URL})")
    except Exception as e:
        print(f"Warning: MongoDB connection check failed: {e}")
    yield
    client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent form-filling assistant API with structured user vault and ML scoring",
    lifespan=lifespan
)

# Configure CORS for Vite Frontend and Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows browser extension and any local dev origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_routes.router, prefix=settings.API_V1_STR)
app.include_router(profile_routes.router, prefix=settings.API_V1_STR)
app.include_router(history_routes.router, prefix=settings.API_V1_STR)
app.include_router(issue_routes.router, prefix=settings.API_V1_STR)
app.include_router(stats_routes.router, prefix=settings.API_V1_STR)
app.include_router(ml_routes.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "formER Backend API",
        "version": settings.VERSION
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to formER API. Visit /docs for interactive Swagger UI."
    }
