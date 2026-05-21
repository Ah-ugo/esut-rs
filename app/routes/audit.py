from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.database import get_database
from app.utils.auth import require_admin

router = APIRouter()


@router.get("/")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    db = get_database()
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if resource:
        query["resource"] = resource
    
    total = await db.audit_logs.count_documents(query)
    skip = (page - 1) * per_page
    
    logs = await db.audit_logs.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    # Enrich with user names
    enriched = []
    for log in logs:
        user = await db.users.find_one({"_id_str": log.get("user_id")})
        enriched.append({
            "id": str(log["_id"]),
            "user_id": log.get("user_id"),
            "user_name": user.get("full_name") if user else "Unknown",
            "action": log.get("action"),
            "resource": log.get("resource"),
            "resource_id": log.get("resource_id"),
            "details": log.get("details", {}),
            "ip_address": log.get("ip_address"),
            "created_at": log.get("created_at"),
        })
    
    return {
        "data": enriched,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }
