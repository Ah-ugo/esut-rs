from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from datetime import datetime
from bson import ObjectId
import pandas as pd
import io
from app.database import get_database
from app.schemas.schemas import StudentCreate
from app.utils.auth import require_admin, get_current_user

router = APIRouter()


def student_out(s: dict, programme_name: str = None) -> dict:
    return {
        "id": str(s["_id"]),
        "matric_number": s.get("matric_number"),
        "full_name": s.get("full_name"),
        "email": s.get("email"),
        "programme_id": s.get("programme_id"),
        "programme_name": programme_name,
        "level": s.get("level"),
        "entry_year": s.get("entry_year"),
        "gender": s.get("gender"),
        "phone": s.get("phone"),
        "address": s.get("address"),
        "photo_url": s.get("photo_url"),
        "cgpa": s.get("cgpa"),
        "degree_class": s.get("degree_class"),
        "created_at": s.get("created_at"),
    }


@router.post("/", status_code=201)
async def create_student(data: StudentCreate, current_user: dict = Depends(require_admin)):
    db = get_database()
    
    if await db.students.find_one({"matric_number": data.matric_number.upper()}):
        raise HTTPException(status_code=400, detail="Matric number already exists")
    
    if not await db.programmes.find_one({"_id": ObjectId(data.programme_id)}):
        raise HTTPException(status_code=404, detail="Programme not found")
    
    doc = data.dict()
    doc["matric_number"] = doc["matric_number"].upper()
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    
    result = await db.students.insert_one(doc)
    
    # Create associated user account
    from app.utils.auth import hash_password
    await db.users.insert_one({
        "email": data.email,
        "full_name": data.full_name,
        "role": "student",
        "password_hash": hash_password(data.matric_number.upper()),  # Default password = matric number
        "matric_number": data.matric_number.upper(),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })
    
    doc["id"] = str(result.inserted_id)
    return {
        "id": doc["id"],
        "matric_number": doc.get("matric_number"),
        "full_name": doc.get("full_name"),
        "email": doc.get("email"),
        "programme_id": doc.get("programme_id"),
        "level": doc.get("level"),
        "entry_year": doc.get("entry_year"),
        "gender": doc.get("gender"),
        "date_of_birth": doc.get("date_of_birth"),
        "phone": doc.get("phone"),
        "address": doc.get("address"),
        "photo_url": doc.get("photo_url"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


@router.get("/")
async def list_students(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    programme_id: Optional[str] = None,
    level: Optional[int] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    query = {}
    if programme_id:
        query["programme_id"] = programme_id
    if level:
        query["level"] = level
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"matric_number": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    
    total = await db.students.count_documents(query)
    skip = (page - 1) * per_page
    students = await db.students.find(query).skip(skip).limit(per_page).to_list(per_page)
    
    result = []
    for s in students:
        prog = await db.programmes.find_one({"_id": ObjectId(s["programme_id"])}) if s.get("programme_id") else None
        result.append(student_out(s, prog.get("name") if prog else None))
    
    return {"data": result, "total": total, "page": page, "per_page": per_page, "total_pages": (total + per_page - 1) // per_page}


@router.get("/{student_id}")
async def get_student(student_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Allow students to get their own profile
    if current_user["role"] == "student":
        s = await db.students.find_one({"matric_number": current_user.get("matric_number")})
        if not s or str(s["_id"]) != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    s = await db.students.find_one({"_id": ObjectId(student_id)})
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    
    prog = await db.programmes.find_one({"_id": ObjectId(s["programme_id"])}) if s.get("programme_id") else None
    return student_out(s, prog.get("name") if prog else None)


@router.get("/by-matric/{matric_number:path}")
async def get_student_by_matric(matric_number: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    s = await db.students.find_one({"matric_number": matric_number.upper()})
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    prog = await db.programmes.find_one({"_id": ObjectId(s["programme_id"])}) if s.get("programme_id") else None
    return student_out(s, prog.get("name") if prog else None)


@router.put("/{student_id}")
async def update_student(student_id: str, data: dict, current_user: dict = Depends(require_admin)):
    db = get_database()
    data["updated_at"] = datetime.utcnow()
    await db.students.update_one({"_id": ObjectId(student_id)}, {"$set": data})
    return {"message": "Student updated"}


@router.delete("/{student_id}")
async def delete_student(student_id: str, current_user: dict = Depends(require_admin)):
    db = get_database()
    await db.students.delete_one({"_id": ObjectId(student_id)})
    return {"message": "Student deleted"}


@router.post("/import-csv")
async def import_students_csv(
    file: UploadFile = File(...),
    programme_id: str = None,
    current_user: dict = Depends(require_admin)
):
    if not file.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files supported")
    
    contents = await file.read()
    
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    
    db = get_database()
    from app.utils.auth import hash_password
    
    success = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            matric = str(row.get("matric_number", "")).strip().upper()
            full_name = str(row.get("full_name", "")).strip()
            email = str(row.get("email", "")).strip().lower()
            
            if not matric or not full_name or not email:
                errors.append({"row": idx + 2, "error": "Missing required fields"})
                continue
            
            if await db.students.find_one({"matric_number": matric}):
                errors.append({"row": idx + 2, "matric_number": matric, "error": "Already exists"})
                continue
            
            prog_id = str(row.get("programme_id", programme_id or ""))
            
            student_doc = {
                "matric_number": matric,
                "full_name": full_name,
                "email": email,
                "programme_id": prog_id,
                "level": int(row.get("level", 100)),
                "entry_year": int(row.get("entry_year", datetime.now().year)),
                "gender": str(row.get("gender", "Male")).strip(),
                "phone": str(row.get("phone", "")).strip() or None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            await db.students.insert_one(student_doc)
            
            # Create user
            if not await db.users.find_one({"email": email}):
                await db.users.insert_one({
                    "email": email,
                    "full_name": full_name,
                    "role": "student",
                    "password_hash": hash_password(matric),
                    "matric_number": matric,
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                })
            
            success.append(matric)
        except Exception as e:
            errors.append({"row": idx + 2, "error": str(e)})
    
    return {
        "message": f"Import complete",
        "total": len(df),
        "success": len(success),
        "errors": len(errors),
        "error_details": errors
    }
