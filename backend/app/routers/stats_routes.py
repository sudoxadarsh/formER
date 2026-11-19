from fastapi import APIRouter, Depends

from ..database import get_db
from ..models import User, FormHistory
from ..schemas import UserStatsResponse
from ..auth import get_current_user

router = APIRouter(prefix="/stats", tags=["Dashboard Analytics"])

@router.get("", response_model=UserStatsResponse)
async def get_user_stats(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    cursor = db.form_history.find({"user_id": str(current_user.id)})
    history_records = [FormHistory(doc) async for doc in cursor]
    
    total_sessions = len(history_records)
    total_fields = sum(h.get("fields_filled_count", 0) or 0 for h in history_records)
    
    # Estimate time saved: average 20 mins per complex application form
    hours_saved = round((total_sessions * 20) / 60, 1)
    time_saved_str = f"{hours_saved}h" if hours_saved >= 1.0 else f"{int(total_sessions * 20)}m"
    if total_sessions == 0:
        time_saved_str = "0h"

    # Accuracy rate calculation
    accuracy = "100%"
    if total_sessions > 0:
        rates = []
        for h in history_records:
            rate_val = h.get("accuracy_rate", "100%")
            try:
                rates.append(float(str(rate_val).replace('%', '')))
            except (ValueError, AttributeError):
                rates.append(100.0)
        if rates:
            avg_acc = sum(rates) / len(rates)
            accuracy = f"{avg_acc:.1f}%"

    return UserStatsResponse(
        forms_filled=total_sessions,
        time_saved=time_saved_str,
        accuracy_rate=accuracy,
        total_fields_populated=total_fields,
        sessions_recorded=total_sessions
    )
