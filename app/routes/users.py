from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.database import get_database
from app.utils.auth import require_admin, get_current_user

router = APIRouter()


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    db = get_database()
    
    query = {}
    if role:
        query["role"] = role
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    
    total = await db.users.count_documents(query)
    skip = (page - 1) * per_page
    users = await db.users.find(query, {"password_hash": 0}).skip(skip).limit(per_page).to_list(per_page)
    
    result = []
    for u in users:
        result.append({
            "id": str(u["_id"]),
            "email": u.get("email"),
            "full_name": u.get("full_name"),
            "role": u.get("role"),
            "matric_number": u.get("matric_number"),
            "staff_id": u.get("staff_id"),
            "is_active": u.get("is_active", True),
            "last_login": u.get("last_login"),
            "created_at": u.get("created_at"),
        })
    
    return {"data": result, "total": total, "page": page, "per_page": per_page}


@router.patch("/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_user: dict = Depends(require_admin)):
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not user.get("is_active", True)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": f"User {'activated' if new_status else 'deactivated'}", "is_active": new_status}


@router.put("/{user_id}")
async def update_user(user_id: str, data: dict, current_user: dict = Depends(require_admin)):
    db = get_database()
    data.pop("password_hash", None)  # Prevent direct hash manipulation
    data.pop("password", None)
    data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": data})
    return {"message": "User updated"}


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db = get_database()
    await db.users.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted"}


@router.post("/reset-password/{user_id}")
async def reset_user_password(user_id: str, data: dict, current_user: dict = Depends(require_admin)):
    new_password = data.get("new_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    from app.utils.auth import hash_password
    db = get_database()
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": hash_password(new_password), "updated_at": datetime.utcnow()}}
    )
    return {"message": "Password reset successfully"}
