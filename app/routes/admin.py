from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime

from bson import ObjectId
from app.database import get_database
from app.utils.auth import require_admin, require_role



router = APIRouter()


@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(require_admin)):
    db = get_database()
    
    total_students = await db.students.count_documents({})
    total_lecturers = await db.users.count_documents({"role": "lecturer"})
    total_courses = await db.courses.count_documents({})
    total_programmes = await db.programmes.count_documents({})
    pending_results = await db.results.count_documents({"status": "pending"})
    approved_results = await db.results.count_documents({"status": "approved"})
    
    # Recent uploads
    recent = await db.results.find({}).sort("created_at", -1).limit(5).to_list(5)
    recent_uploads = []
    for r in recent:
        # Prefer stable lookup via matric_number (results docs should store this).
        # Fall back to student_id if available (legacy documents).
        student = None
        if r.get("matric_number"):
            student = await db.students.find_one({"matric_number": str(r.get("matric_number")).upper()})
        elif r.get("student_id"):
            try:
                student = await db.students.find_one({"_id": ObjectId(r["student_id"])})
            except Exception:
                student = None

        course = None
        if r.get("course_id"):
            try:
                course = await db.courses.find_one({"_id": ObjectId(r["course_id"])})
            except Exception:
                course = None

        recent_uploads.append({
            "id": str(r["_id"]),
            "student_name": student.get("full_name") if student else "Unknown",
            "matric_number": student.get("matric_number") if student else (r.get("matric_number") or ""),
            "course_code": course.get("code") if course else "",
            "score": r.get("score"),
            "grade": r.get("grade"),
            "status": r.get("status"),
            "created_at": r.get("created_at"),
        })
    
    # GPA distribution
    approved_results_docs = await db.results.find({"status": "approved"}).to_list(10000)
    gpa_dist = {"A (5.0)": 0, "B (4.0)": 0, "C (3.0)": 0, "D (2.0)": 0, "E (1.0)": 0, "F (0.0)": 0}
    for r in approved_results_docs:
        grade = r.get("grade", "F")
        key_map = {"A": "A (5.0)", "B": "B (4.0)", "C": "C (3.0)", "D": "D (2.0)", "E": "E (1.0)", "F": "F (0.0)"}
        k = key_map.get(grade, "F (0.0)")
        gpa_dist[k] += 1
    
    return {
        "total_students": total_students,
        "total_lecturers": total_lecturers,
        "total_courses": total_courses,
        "total_programmes": total_programmes,
        "pending_results": pending_results,
        "approved_results": approved_results,
        "recent_uploads": recent_uploads,
        "gpa_distribution": gpa_dist,
    }


@router.post("/grading-config")
async def set_grading_config(config: dict, current_user: dict = Depends(require_admin)):
    db = get_database()
    programme_id = config.get("programme_id")
    grades = config.get("grades", [])
    
    await db.grading_configs.update_one(
        {"programme_id": programme_id},
        {"$set": {"programme_id": programme_id, "grades": grades, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return {"message": "Grading configuration saved"}


@router.get("/grading-config")
async def get_grading_config(
    programme_id: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    db = get_database()
    config = await db.grading_configs.find_one({"programme_id": programme_id})
    return config or {"programme_id": programme_id, "grades": []}


@router.post("/current-session")
async def set_current_session(
    payload: Dict[str, Any],
    current_user: dict = Depends(require_admin),
):
    """Set the active academic session for a programme."""
    db = get_database()
    programme_id = payload.get("programme_id")
    session = payload.get("session")

    if not session:
        raise HTTPException(status_code=422, detail="session is required")

    # Store as programme-specific or global (programme_id can be None)
    await db.current_sessions.update_one(
        {"programme_id": programme_id},
        {"$set": {"programme_id": programme_id, "session": session, "updated_at": datetime.utcnow()}},
        upsert=True,
    )
    return {"message": "Current session updated", "programme_id": programme_id, "session": session}


@router.get("/current-session")
async def get_current_session(
    programme_id: Optional[str] = None,
    current_user: dict = Depends(require_role("admin", "lecturer", "student")),
):
    """Get the active academic session for a programme.

    Read access is allowed for admin/lecturers/students. Session updates remain admin-only.
    """
    db = get_database()
    doc = await db.current_sessions.find_one({"programme_id": programme_id})
    return doc or {"programme_id": programme_id, "session": None}



@router.get("/pending-results")
async def get_pending_results(

    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_admin)
):
    db = get_database()
    
    total = await db.results.count_documents({"status": "pending"})
    skip = (page - 1) * per_page
    results = await db.results.find({"status": "pending"}).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    enriched = []
    for r in results:
        student = await db.students.find_one({"_id": ObjectId(r["student_id"])}) if r.get("student_id") else None
        course = await db.courses.find_one({"_id": ObjectId(r["course_id"])}) if r.get("course_id") else None
        enriched.append({
            "id": str(r["_id"]),
            "student_name": student.get("full_name") if student else "Unknown",
            "matric_number": student.get("matric_number") if student else "",
            "course_code": course.get("code") if course else "",
            "course_title": course.get("title") if course else "",
            "score": r.get("score"),
            "grade": r.get("grade"),
            "session": r.get("session"),
            "semester": r.get("semester"),
            "status": r.get("status"),
            "created_at": r.get("created_at"),
        })
    
    return {"data": enriched, "total": total, "page": page, "per_page": per_page}
