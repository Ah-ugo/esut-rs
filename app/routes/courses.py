from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.database import get_database
from app.schemas.schemas import CourseCreate, CourseAssignment
from app.utils.auth import require_lecturer, require_admin

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_course(course_data: CourseCreate, current_user: dict = Depends(require_admin)):
    db = get_database()
    
    # Check if course code already exists
    if await db.courses.find_one({"code": course_data.code.upper()}):
        raise HTTPException(status_code=400, detail="Course code already exists")
    
    # Resolve programme_code to verify it exists
    prog = await db.programmes.find_one({"code": course_data.programme_code.upper()})
    if not prog:
        raise HTTPException(status_code=404, detail=f"Programme with code {course_data.programme_code} not found")
        
    course_doc = course_data.dict()
    course_doc["code"] = course_doc["code"].upper()
    course_doc["programme_id"] = str(prog["_id"]) # Store the ID reference internally
    course_doc["created_at"] = datetime.utcnow()
    course_doc["updated_at"] = datetime.utcnow()
    
    result = await db.courses.insert_one(course_doc)
    course_doc["id"] = str(result.inserted_id)
    if "_id" in course_doc: del course_doc["_id"]
    return course_doc

@router.get("/", response_model=Dict[str, Any])
async def list_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1),
    programme_id: Optional[str] = None,
    semester: Optional[str] = None,
    level: Optional[int] = None,
    search: Optional[str] = None
):
    db = get_database()
    match_query = {}
    if programme_id:
        match_query["programme_id"] = programme_id
    if semester:
        match_query["semester"] = semester
    if level:
        match_query["level"] = level
    if search:
        match_query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}}
        ]

    total = await db.courses.count_documents(match_query)
    skip = (page - 1) * per_page

    pipeline = [
        {"$match": match_query},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},
        {
            "$lookup": {
                "from": "programmes",
                "let": {"p_id": "$programme_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$$p_id"]}}}
                ],
                "as": "prog"
            }
        },
        {
            "$addFields": {
                "id": {"$toString": "$_id"},
                "programme_name": {"$arrayElemAt": ["$prog.name", 0]}
            }
        },
        {"$project": {"_id": 0, "prog": 0}}
    ]

    courses = await db.courses.aggregate(pipeline).to_list(length=per_page)

    return {
        "data": courses,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/{course_id}")
async def get_course(course_id: str):
    db = get_database()
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course["id"] = str(course.pop("_id"))
    return course

@router.post("/{course_id}/assign-lecturer")
async def assign_lecturer(course_id: str, data: CourseAssignment, current_user: dict = Depends(require_admin)):
    db = get_database()
    
    # Verify lecturer exists
    lecturer = await db.users.find_one({"_id": ObjectId(data.lecturer_id), "role": "lecturer"})
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
        
    res = await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": {
            "lecturer_id": data.lecturer_id,
            "session": data.session,
            "updated_at": datetime.utcnow()
        }}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Lecturer assigned successfully"}

@router.put("/{course_id}")
async def update_course(course_id: str, data: dict, current_user: dict = Depends(require_admin)):
    db = get_database()
    data["updated_at"] = datetime.utcnow()
    res = await db.courses.update_one({"_id": ObjectId(course_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course updated"}

@router.delete("/{course_id}")
async def delete_course(course_id: str, current_user: dict = Depends(require_admin)):
    db = get_database()
    res = await db.courses.delete_one({"_id": ObjectId(course_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted"}

@router.get("/lecturer/{lecturer_id}")
async def get_lecturer_courses(lecturer_id: str, session: str = None, current_user: dict = Depends(require_lecturer)):
    db = get_database()
    # Find courses where this user is the assigned lecturer
    query = {"lecturer_id": lecturer_id}
    if session:
        query["session"] = session
        
    courses = await db.courses.find(query).to_list(length=100)
    for c in courses:
        c["id"] = str(c.pop("_id"))
    return {"courses": courses}