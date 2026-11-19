from typing import Optional
from fastapi import APIRouter, Depends, status

from ..database import get_db
from ..models import User, IssueReport, utc_now
from ..schemas import IssueReportCreate, IssueReportResponse
from ..auth import get_current_user, get_optional_current_user

router = APIRouter(prefix="/issues", tags=["Support & Issues"])

@router.post("", response_model=IssueReportResponse, status_code=status.HTTP_201_CREATED)
async def report_issue(
    issue_in: IssueReportCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db = Depends(get_db)
):
    issue_doc = {
        "user_id": str(current_user.id) if current_user else None,
        "issue_type": issue_in.issue_type,
        "portal_url": issue_in.portal_url,
        "description": issue_in.description,
        "diagnostic_data": issue_in.diagnostic_data or {},
        "created_at": utc_now()
    }
    result = await db.issue_reports.insert_one(issue_doc)
    issue_doc["_id"] = result.inserted_id
    return IssueReport(issue_doc)

@router.get("", response_model=list[IssueReportResponse])
async def get_user_issues(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    cursor = db.issue_reports.find({"user_id": str(current_user.id)}).sort("created_at", -1)
    return [IssueReport(doc) async for doc in cursor]
