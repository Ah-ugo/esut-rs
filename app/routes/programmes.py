from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.database import get_database
from app.schemas.schemas import ProgrammeCreate, CourseCreate, StudentCreate
from app.utils.auth import require_admin, require_lecturer, get_current_user

# ─── PROGRAMMES ────────────────────────────────────────────────
router = APIRouter()


@router.post("/", status_code=201)
async def create_programme(data: ProgrammeCreate, current_user: dict = Depends(require_admin)):
    db = get_database()
    if await db.programmes.find_one({"code": data.code.upper()}):
        raise HTTPException(status_code=400, detail="Programme code already exists")
    
    doc = data.dict()
    doc["code"] = doc["code"].upper()
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    
    result = await db.programmes.insert_one(doc)
    return {
        "id": str(result.inserted_id),
        "name": doc.get("name"),
        "code": doc.get("code"),
        "faculty": doc.get("faculty"),
        "department": doc.get("department"),
        "duration_years": doc.get("duration_years"),
        "description": doc.get("description"),
        "created_at": doc.get("created_at"),
    }


@router.get("/")
async def list_programmes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    total = await db.programmes.count_documents({})
    skip = (page - 1) * per_page
    progs = await db.programmes.find({}).skip(skip).limit(per_page).to_list(per_page)
    
    result = []
    for p in progs:
        count = await db.students.count_documents({"programme_id": str(p["_id"])})
        result.append({
            "id": str(p["_id"]),
            "name": p.get("name"),
            "code": p.get("code"),
            "faculty": p.get("faculty"),
            "department": p.get("department"),
            "duration_years": p.get("duration_years"),
            "description": p.get("description"),
            "total_students": count,
            "created_at": p.get("created_at"),
        })
    
    return {"data": result, "total": total, "page": page, "per_page": per_page}


@router.get("/{programme_id}")
async def get_programme(programme_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    p = await db.programmes.find_one({"_id": ObjectId(programme_id)})
    if not p:
        raise HTTPException(status_code=404, detail="Programme not found")
    p["id"] = str(p["_id"])
    del p["_id"]
    return p


@router.put("/{programme_id}")
async def update_programme(programme_id: str, data: dict, current_user: dict = Depends(require_admin)):
    db = get_database()
    data["updated_at"] = datetime.utcnow()
    await db.programmes.update_one({"_id": ObjectId(programme_id)}, {"$set": data})
    return {"message": "Programme updated"}


@router.delete("/{programme_id}")
async def delete_programme(programme_id: str, current_user: dict = Depends(require_admin)):
    db = get_database()
    await db.programmes.delete_one({"_id": ObjectId(programme_id)})
    return {"message": "Programme deleted"}
