from fastapi import APIRouter, Depends, HTTPException, Response
from bson import ObjectId
from app.database import get_database
from app.utils.auth import get_current_user
from app.services.transcript_service import generate_transcript_pdf
from app.services.grading_service import calculate_grade, get_grading_system, get_degree_classification

router = APIRouter()


@router.get("/student/{student_id}")
async def get_student_transcript_data(
    student_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    obj_id = ObjectId(student_id)
    student = await db.students.find_one({"_id": obj_id})
    user_id = None
    
    if not student:
        user = await db.users.find_one({"_id": obj_id})
        if user and user.get("matric_number"):
            user_id = str(user["_id"])
            student = await db.students.find_one({"matric_number": user["matric_number"].upper()})
    else:
        user = await db.users.find_one({"matric_number": student["matric_number"].upper(), "role": "student"})
        if user:
            user_id = str(user["_id"])
    
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    all_student_ids = list(set(filter(None, [str(student["_id"]), user_id])))
    
    # Students can only access their own transcript
    if current_user["role"] == "student":
        s = await db.students.find_one({"matric_number": current_user.get("matric_number")})
        if not s or str(s["_id"]) not in all_student_ids:
            raise HTTPException(status_code=403, detail="Access denied")
    
    programme = await db.programmes.find_one({"_id": ObjectId(student.get("programme_id", ""))})
    
    # Get all approved results
    results = await db.results.find(
        {"student_id": {"$in": all_student_ids}, "status": "approved"}
    ).sort([("session", 1), ("semester", 1)]).to_list(1000)
    
    # Group by session + semester
    semester_map = {}
    for result in results:
        # Standardize point field
        result["grade_point"] = result.get("grade_point", result.get("points", 0))
        
        key = f"{result['session']}_{result['semester']}"
        if key not in semester_map:
            semester_map[key] = []
        
        course = await db.courses.find_one({"_id": ObjectId(result["course_id"])})
        result["course_code"] = course.get("code", "") if course else ""
        result["course_title"] = course.get("title", "") if course else ""
        result["course_units"] = course.get("units", 0) if course else 0
        semester_map[key].append(result)
    
    semesters = []
    all_results = []
    
    for key, sem_results in semester_map.items():
        session, semester = key.rsplit("_", 1)
        total_units = sum(r.get("course_units", 0) for r in sem_results)
        total_points = sum(r.get("course_units", 0) * r.get("grade_point", 0) for r in sem_results)
        gpa = round(total_points / total_units, 2) if total_units > 0 else 0.0
        
        semesters.append({
            "session": session,
            "semester": semester,
            "gpa": gpa,
            "total_units": total_units,
            "results": [
                {
                    "id": str(r["_id"]),
                    "course_code": r.get("course_code", ""),
                    "course_title": r.get("course_title", ""),
                    "course_units": r.get("course_units", 0),
                    "score": r.get("score", 0),
                    "grade": r.get("grade", ""),
                    "grade_point": r.get("grade_point", 0),
                }
                for r in sem_results
            ]
        })
        all_results.extend(sem_results)
    
    # Calculate CGPA
    best_results = {}
    for r in all_results:
        cid = r["course_id"]
        if cid not in best_results or r.get("grade_point", 0) > best_results[cid].get("grade_point", 0):
            best_results[cid] = r
    
    total_units = sum(r.get("course_units", 0) for r in best_results.values())
    total_points = sum(r.get("course_units", 0) * r.get("grade_point", 0) for r in best_results.values())
    cgpa = round(total_points / total_units, 2) if total_units > 0 else 0.0
    degree_class = get_degree_classification(cgpa)
    
    return {
        "student": {
            "id": str(student["_id"]),
            "full_name": student.get("full_name"),
            "matric_number": student.get("matric_number"),
            "email": student.get("email"),
            "gender": student.get("gender"),
            "entry_year": student.get("entry_year"),
            "level": student.get("level"),
            "programme_id": student.get("programme_id"),
        },
        "programme": {
            "name": programme.get("name", "") if programme else "",
            "code": programme.get("code", "") if programme else "",
            "faculty": programme.get("faculty", "") if programme else "",
            "department": programme.get("department", "") if programme else "",
            "duration_years": programme.get("duration_years", 4) if programme else 4,
        } if programme else {},
        "semesters": semesters,
        "cgpa": cgpa,
        "total_units": total_units,
        "degree_class": degree_class,
    }


@router.get("/student/{student_id}/pdf")
async def download_transcript_pdf(
    student_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if current_user["role"] == "student":
        s = await db.students.find_one({"matric_number": current_user.get("matric_number")})
        if not s or str(s["_id"]) != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    transcript_data = await get_student_transcript_data(student_id, current_user)
    
    programme = await db.programmes.find_one({"_id": ObjectId(student.get("programme_id", ""))})
    
    verification_url = f"https://esut.edu.ng/verify/{student.get('matric_number', '')}"
    
    pdf_bytes = generate_transcript_pdf(
        student=transcript_data["student"],
        programme=transcript_data["programme"],
        semesters=transcript_data["semesters"],
        cgpa=transcript_data["cgpa"],
        degree_class=transcript_data["degree_class"],
        verification_url=verification_url,
    )
    
    matric = student.get("matric_number", "transcript").replace("/", "_")
    filename = f"ESUT_Transcript_{matric}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


@router.get("/verify/{matric_number:path}")
async def verify_transcript(matric_number: str):
    """Public endpoint to verify transcript authenticity"""
    db = get_database()
    
    student = await db.students.find_one({"matric_number": matric_number.upper()})
    if not student:
        return {"verified": False, "message": "Student not found"}
    
    user = await db.users.find_one({"matric_number": student["matric_number"].upper(), "role": "student"})
    all_student_ids = [str(student["_id"])]
    if user:
        all_student_ids.append(str(user["_id"]))

    programme = await db.programmes.find_one({"_id": ObjectId(student.get("programme_id", ""))})
    
    results = await db.results.find(
        {"student_id": {"$in": all_student_ids}, "status": "approved"}
    ).to_list(1000)
    
    total_units = 0
    total_points = 0.0
    best_results = {}
    
    for r in results:
        course = await db.courses.find_one({"_id": ObjectId(r["course_id"])})
        units = course.get("units", 0) if course else 0
        r["course_units"] = units
        
        cid = r["course_id"]
        if cid not in best_results or r.get("grade_point", 0) > best_results[cid].get("grade_point", 0):
            best_results[cid] = r
    
    for r in best_results.values():
        total_units += r.get("course_units", 0)
        total_points += r.get("course_units", 0) * r.get("grade_point", 0)
    
    cgpa = round(total_points / total_units, 2) if total_units > 0 else 0.0
    degree_class = get_degree_classification(cgpa)
    
    return {
        "verified": True,
        "student_name": student.get("full_name"),
        "matric_number": student.get("matric_number"),
        "programme": programme.get("name", "") if programme else "",
        "cgpa": cgpa,
        "degree_class": degree_class,
        "verification_timestamp": "2024-01-01T00:00:00Z",
    }
