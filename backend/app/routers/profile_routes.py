from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..models import User, Profile, utc_now
from ..schemas import ProfileUpdate, ProfileResponse
from ..auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile Vault"])

def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Recursively flattens nested profile dictionaries for quick lookup by extension."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, elem in enumerate(v):
                if isinstance(elem, dict):
                    items.extend(flatten_dict(elem, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", elem))
        else:
            if v is not None and str(v).strip() != "":
                items.append((new_key, str(v)))
    return dict(items)

@router.get("", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    profile = await db.profiles.find_one({"user_id": str(current_user.id)})
    if not profile:
        now = utc_now()
        profile_data = {
            "user_id": str(current_user.id),
            "personal_data": {"full_name": current_user.name},
            "contact_data": {"email": current_user.email},
            "education_data": {},
            "work_data": [],
            "documents_data": {},
            "preferences": {},
            "updated_at": now
        }
        res = await db.profiles.insert_one(profile_data)
        profile_data["_id"] = res.inserted_id
        profile = profile_data
    return Profile(profile)

@router.put("", response_model=ProfileResponse)
async def update_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    profile = await db.profiles.find_one({"user_id": str(current_user.id)})
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    updated_fields = {"updated_at": utc_now()}

    if profile_in.personal_data is not None:
        merged = dict(profile.get("personal_data") or {})
        merged.update(profile_in.personal_data)
        updated_fields["personal_data"] = merged
        profile["personal_data"] = merged

    if profile_in.contact_data is not None:
        merged = dict(profile.get("contact_data") or {})
        merged.update(profile_in.contact_data)
        updated_fields["contact_data"] = merged
        profile["contact_data"] = merged

    if profile_in.education_data is not None:
        merged = dict(profile.get("education_data") or {})
        merged.update(profile_in.education_data)
        updated_fields["education_data"] = merged
        profile["education_data"] = merged

    if profile_in.work_data is not None:
        updated_fields["work_data"] = profile_in.work_data
        profile["work_data"] = profile_in.work_data

    if profile_in.documents_data is not None:
        merged = dict(profile.get("documents_data") or {})
        merged.update(profile_in.documents_data)
        updated_fields["documents_data"] = merged
        profile["documents_data"] = merged

    if profile_in.preferences is not None:
        merged = dict(profile.get("preferences") or {})
        merged.update(profile_in.preferences)
        updated_fields["preferences"] = merged
        profile["preferences"] = merged

    await db.profiles.update_one({"_id": profile["_id"]}, {"$set": updated_fields})
    profile["updated_at"] = updated_fields["updated_at"]
    return Profile(profile)

@router.get("/flattened", response_model=dict[str, str])
async def get_flattened_profile(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Returns a flat key-value dictionary designed specifically for browser extension autofill."""
    profile = await db.profiles.find_one({"user_id": str(current_user.id)})
    if not profile:
        return {}

    full_payload = {
        "personal": profile.get("personal_data") or {},
        "contact": profile.get("contact_data") or {},
        "education": profile.get("education_data") or {},
        "work": profile.get("work_data") or [],
    }
    return flatten_dict(full_payload)

@router.get("/export")
async def export_profile(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    profile = await db.profiles.find_one({"user_id": str(current_user.id)})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    updated_at_val = profile.get("updated_at")
    exported_at_str = updated_at_val.isoformat() if hasattr(updated_at_val, "isoformat") else str(updated_at_val)

    return {
        "user": {"name": current_user.name, "email": current_user.email},
        "personal": profile.get("personal_data", {}),
        "contact": profile.get("contact_data", {}),
        "education": profile.get("education_data", {}),
        "work": profile.get("work_data", []),
        "preferences": profile.get("preferences", {}),
        "exported_at": exported_at_str
    }
