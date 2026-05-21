from datetime import datetime
from typing import Optional
from fastapi import Request
from app.database import get_database


async def log_action(
    user_id: str,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
):
    db = get_database()
    
    ip_address = None
    if request and request.client:
        ip_address = request.client.host
    
    log_doc = {
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "details": details or {},
        "ip_address": ip_address,
        "created_at": datetime.utcnow(),
    }
    
    await db.audit_logs.insert_one(log_doc)
