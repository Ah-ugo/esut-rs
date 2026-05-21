from fastapi import APIRouter, HTTPException, Depends, Request, status
from datetime import datetime
from bson import ObjectId
from app.database import get_database
from app.schemas.schemas import UserCreate, UserLogin, TokenResponse, UserOut
from app.utils.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user
)
from app.services.audit_service import log_action

router = APIRouter()


def serialize_user(user: dict) -> dict:
    if not user:
        return user
    user["id"] = str(user.pop("_id"))
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, request: Request):
    db = get_database()
    
    # Check duplicate email
    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check duplicate matric number
    if user_data.matric_number and await db.users.find_one({"matric_number": user_data.matric_number}):
        raise HTTPException(status_code=400, detail="Matriculation number already registered")
    
    user_doc = {
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role,
        "password_hash": hash_password(user_data.password),
        "matric_number": user_data.matric_number,
        "staff_id": user_data.staff_id,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    user_id = str(result.inserted_id)
    access_token = create_access_token({"sub": user_id, "role": user_data.role})
    refresh_token = create_refresh_token({"sub": user_id})
    
    await log_action(user_id, "REGISTER", "user", user_id, {"role": user_data.role}, request)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "matric_number": user_data.matric_number,
            "staff_id": user_data.staff_id,
            "is_active": True,
            "created_at": user_doc["created_at"],
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    db = get_database()
    
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account has been deactivated")
    
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user_id})
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    await log_action(user_id, "LOGIN", "user", user_id, {}, request)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "matric_number": user.get("matric_number"),
            "staff_id": user.get("staff_id"),
            "is_active": user.get("is_active", True),
            "created_at": user["created_at"],
        }
    }


@router.post("/refresh")
async def refresh_token(token_data: dict):
    token = token_data.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    new_access_token = create_access_token({"sub": user_id, "role": user["role"]})
    return {
        "access_token": new_access_token,
        "refresh_token": token,  # Return the same refresh token or rotate it
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user.get("is_active", True),
            "created_at": user["created_at"]
        }
    }


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "matric_number": current_user.get("matric_number"),
        "staff_id": current_user.get("staff_id"),
        "is_active": current_user.get("is_active", True),
        "created_at": current_user["created_at"],
    }


@router.post("/change-password")
async def change_password(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Both old and new passwords required")
    
    if not verify_password(old_password, current_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    db = get_database()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password_hash": hash_password(new_password), "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Password changed successfully"}
