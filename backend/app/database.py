# pyrefly: ignore [missing-import]
import motor.motor_asyncio
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  
from .config import settings

# Create Motor client with 5s timeout
client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(
    settings.MONGODB_URL,
    serverSelectionTimeoutMS=5000
)
database: AsyncIOMotorDatabase = client.get_database(settings.DATABASE_NAME)

# Dependency for FastAPI routes
async def get_db() -> AsyncIOMotorDatabase:
    return database
