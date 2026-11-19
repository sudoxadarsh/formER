from fastapi import APIRouter, Depends, status

from ..database import get_db
from ..models import User, FormHistory, utc_now
from ..schemas import FormHistoryCreate, FormHistoryResponse
from ..auth import get_current_user

router = APIRouter(prefix="/history", tags=["Form History"])

@router.get("", response_model=list[FormHistoryResponse])
async def get_history(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    cursor = db.form_history.find({"user_id": str(current_user.id)}).sort("created_at", -1)
    return [FormHistory(doc) async for doc in cursor]

@router.post("", response_model=FormHistoryResponse, status_code=status.HTTP_201_CREATED)
async def record_history(
    entry: FormHistoryCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    history_record = {
        "user_id": str(current_user.id),
        "portal_name": entry.portal_name,
        "portal_url": entry.portal_url,
        "fields_filled_count": entry.fields_filled_count,
        "accuracy_rate": entry.accuracy_rate,
        "filled_fields": entry.filled_fields,
        "created_at": utc_now()
    }
    result = await db.form_history.insert_one(history_record)
    history_record["_id"] = result.inserted_id
    return FormHistory(history_record)

@router.delete("/purge", status_code=status.HTTP_200_OK)
async def purge_history(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    await db.form_history.delete_many({"user_id": str(current_user.id)})
    return {"message": "Field cache and audit history purged successfully"}
