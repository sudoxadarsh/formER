from datetime import datetime, timezone
from typing import Any, Optional
# pyrefly: ignore [missing-import]
from bson import ObjectId

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def to_object_id(val: Any) -> Any:
    if isinstance(val, str) and ObjectId.is_valid(val):
        return ObjectId(val)
    return val

class MongoDocument(dict):
    """
    Base dictionary wrapper for MongoDB documents that:
    1. Synchronizes MongoDB '_id' and string 'id'.
    2. Supports both dict indexing (doc['field']) and dot attribute access (doc.field).
    3. Serializes cleanly into Pydantic API response models.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "_id" in self and "id" not in self:
            self["id"] = str(self["_id"])
        elif "id" in self and "_id" not in self:
            self["_id"] = to_object_id(self["id"])
            self["id"] = str(self["id"])

    def __getattr__(self, name: str) -> Any:
        if name == "id":
            return str(self.get("_id", self.get("id", "")))
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name: str, value: Any):
        self[name] = value


class User(MongoDocument):
    """User document in 'users' collection."""
    id: str
    email: str
    name: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime


class Profile(MongoDocument):
    """Profile document in 'profiles' collection."""
    id: str
    user_id: str
    personal_data: dict[str, Any]
    contact_data: dict[str, Any]
    education_data: dict[str, Any]
    work_data: list[dict[str, Any]]
    documents_data: dict[str, Any]
    preferences: dict[str, Any]
    updated_at: datetime


class FormHistory(MongoDocument):
    """Form fill session log in 'form_history' collection."""
    id: str
    user_id: str
    portal_name: str
    portal_url: str
    fields_filled_count: int
    accuracy_rate: str
    filled_fields: list[dict[str, Any]]
    created_at: datetime


class IssueReport(MongoDocument):
    """Diagnostic issue report in 'issue_reports' collection."""
    id: str
    user_id: Optional[str]
    issue_type: str
    portal_url: Optional[str]
    description: str
    diagnostic_data: dict[str, Any]
    created_at: datetime
