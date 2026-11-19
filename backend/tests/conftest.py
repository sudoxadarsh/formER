import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.database import get_db
from app.main import app

TEST_DB_NAME = "former_test_db"
sync_client = MongoClient("mongodb://127.0.0.1:27017")

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    sync_client.drop_database(TEST_DB_NAME)
    yield
    sync_client.drop_database(TEST_DB_NAME)
    sync_client.close()

@pytest.fixture(autouse=True)
def clear_collections():
    db = sync_client[TEST_DB_NAME]
    for c in db.list_collection_names():
        db[c].delete_many({})
    yield

@pytest.fixture
def client():
    test_motor_client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
    test_db = test_motor_client[TEST_DB_NAME]

    async def override_get_db():
        return test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_c:
        yield test_c
    app.dependency_overrides.clear()
    test_motor_client.close()
