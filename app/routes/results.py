from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile, Query
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from bson import ObjectId
from app.database import get_database
from app.schemas.schemas import (
    ResultCreate, BulkResultUpload, ResultOut, ResultStatus, 
    AcademicSummary, SemesterGPA, StudentOut, Semester
)
from app.utils.auth import get_current_user, require_lecturer, require_admin
from app.services.grading_service import get_degree_classification, calculate_grade, get_grading_system

router = APIRouter()

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def add_result(result_data: ResultCreate, current_user: dict = Depends(require_lecturer)):
    db = get_database()
    
    # Verify course is assigned to this lecturer
    course_assignment = await db.courses.find_one({
        "code": result_data.course_code.upper(),
        "lecturer_id": str(current_user["_id"]),
        "session": result_data.session,
        "semester": result_data.semester
    })
    if not course_assignment:
        raise HTTPException(status_code=403, detail=f"Course {result_data.course_code} is not assigned to you for {result_data.session} ({result_data.semester} semester)")

    # Resolve matric_number to student profile ID (db.students)
    student_profile = await db.students.find_one({"matric_number": result_data.matric_number.upper()})
    if not student_profile:
        raise HTTPException(status_code=404, detail=f"Student with matric number {result_data.matric_number} not found")
    student_id = str(student_profile["_id"])

    # Resolve course_code to course_id
    course = await db.courses.find_one({"code": result_data.course_code.upper()})
    if not course:
        raise HTTPException(status_code=404, detail=f"Course with code {result_data.course_code} not found")
    course_id = str(course["_id"])

    # Use central grading service
    programme_id = course.get("programme_id")
    grading_system = await get_grading_system(programme_id)
    grade, points, remark = calculate_grade(result_data.score, grading_system)
    
    result_doc = {
        "student_id": student_id,
        "matric_number": result_data.matric_number, # Store matric_number for easier lookup/display
        "course_id": course_id,
        "course_code": result_data.course_code,     # Store course_code for easier lookup/display
        "lecturer_id": str(current_user["_id"]),
        "score": result_data.score,
        "grade": grade,
        "grade_point": points,
        "session": result_data.session,
        "semester": result_data.semester,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    res = await db.results.insert_one(result_doc)
    result_doc["id"] = str(res.inserted_id)
    if "_id" in result_doc: result_doc["_id"] = str(result_doc["_id"])
    return result_doc

@router.post("/upload-csv", status_code=status.HTTP_201_CREATED)
async def upload_csv_results(
    file: UploadFile = File(...),
    course_code: str = Query(...),
    session: str = Query(...),
    semester: Semester = Query(...),
    current_user: dict = Depends(require_lecturer)
):
    import pandas as pd
    import io
    
    db = get_database()
    
    # Verify course is assigned to this lecturer
    assigned_course = await db.courses.find_one({
        "code": course_code.upper(),
        "lecturer_id": str(current_user["_id"]),
        "session": session,
        "semester": semester
    })
    
    if not assigned_course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Course {course_code} is not assigned to you for {session} {semester} semester"
        )

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    
    # Standardize headers
    df.columns = [c.lower().strip() for c in df.columns]
    
    grading_system = await get_grading_system(assigned_course.get("programme_id"))
    results_to_insert = []
    errors = []

    for idx, row in df.iterrows():
        matric = str(row.get('matric_number', '')).strip().upper()
        score = float(row.get('score', 0))
        
        student = await db.students.find_one({"matric_number": matric})
        if not student:
            errors.append(f"Row {idx+2}: Student {matric} not found")
            continue
            
        grade, points, _ = calculate_grade(score, grading_system)
        
        results_to_insert.append({
            "student_id": str(student["_id"]),
            "matric_number": matric,
            "course_id": str(assigned_course["_id"]),
            "course_code": course_code.upper(),
            "lecturer_id": str(current_user["_id"]),
            "score": score,
            "grade": grade,
            "grade_point": points,
            "session": session,
            "semester": semester,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

    if results_to_insert:
        # Use upsert logic or delete old pending entries to avoid index collision
        for doc in results_to_insert:
            await db.results.update_one(
                {
                    "student_id": doc["student_id"],
                    "course_id": doc["course_id"],
                    "session": doc["session"],
                    "semester": doc["semester"]
                },
                {"$set": doc},
                upsert=True
            )
            
    return {
        "message": f"Processed {len(results_to_insert)} results",
        "errors": errors
    }

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_upload_results(upload_data: BulkResultUpload, current_user: dict = Depends(require_lecturer)):
    db = get_database()
    results_to_insert = []
    
    # Resolve course_code to course_id
    course = await db.courses.find_one({"code": upload_data.course_code.upper()})
    if not course:
        raise HTTPException(status_code=404, detail=f"Course with code {upload_data.course_code} not found")

    # Verify course is assigned to this lecturer
    if (course.get("lecturer_id") != str(current_user["_id"]) or 
        course.get("session") != upload_data.session or
        course.get("semester") != upload_data.semester):
        raise HTTPException(status_code=403, detail="You are not assigned to this course for the selected session/semester")

    for entry in upload_data.results:
        student_profile = await db.students.find_one({"matric_number": entry.matric_number.upper()})
        if not student_profile:
            continue # Skip invalid students or return error list
            
        grade, points = calculate_grade(entry.score)
        results_to_insert.append({
            "student_id": str(student_profile["_id"]),
            "course_id": str(course["_id"]),
            "course_code": course["code"],
            "matric_number": student_profile["matric_number"],
            "lecturer_id": str(current_user["_id"]),
            "score": entry.score,
            "grade": grade,
            "grade_point": points,
            "session": upload_data.session,
            "semester": upload_data.semester,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
    if results_to_insert:
        await db.results.insert_many(results_to_insert)
        
    return {"message": f"Successfully processed {len(results_to_insert)} results"}

@router.get("/student/{student_id}", response_model=List[ResultOut])
async def get_student_results(student_id: str):
    db = get_database()
    
    # Resolve all possible IDs for the student (User ID and Profile ID)
    student_ids = [student_id]
    try:
        obj_id = ObjectId(student_id)
        # If student_id is Profile ID, find the User ID
        profile = await db.students.find_one({"_id": obj_id})
        if profile:
            user = await db.users.find_one({"matric_number": profile["matric_number"].upper(), "role": "student"})
            if user:
                student_ids.append(str(user["_id"]))
        else:
            # If student_id is User ID, find the Profile ID
            user = await db.users.find_one({"_id": obj_id})
    except Exception:
        # If conversion to ObjectId fails, treat student_id as a string ID
        pass
    # Build aggregation pipeline to join courses and enrich result fields
    pipeline = [
        {"$match": {"student_id": {"$in": student_ids}}},
        {
            "$lookup": {
                "from": "courses",
                "let": {"c_id": "$course_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$${c_id}"]}}}
                ],
                "as": "course_info"
            }
        },
        {"$unwind": {"path": "$course_info", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "id": {"$toString": "$_id"},
                "grade_point": {"$ifNull": ["$grade_point", "$points", 0.0]},
                "course_code": "$course_info.code",
                "course_title": "$course_info.title",
                "course_units": "$course_info.units",
                # Include status and level for summary calculations
                "status": "$status",
                "level": "$level"
            }
        },
        {"$project": {"course_info": 0, "_id": 0}}
    ]
    cursor = db.results.aggregate(pipeline)
    return [doc async for doc in cursor]

@router.get("/student/{student_id}/summary", response_model=AcademicSummary)
async def get_student_academic_summary(student_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Resolve student record (handling potential UserID vs StudentID mismatch)
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        user = await db.users.find_one({"_id": ObjectId(student_id)})
        if user and user.get("matric_number"):
            student = await db.students.find_one({"matric_number": user["matric_number"]})
            
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    # Get all approved results with course info
    results = await get_student_results(str(student["_id"]))
    approved_results = [r for r in results if r["status"] == "approved"]
    
    # Group by session and semester
    sem_data = {}
    for r in approved_results:
        key = f"{r['session']}-{r['semester']}"
        if key not in sem_data:
            sem_data[key] = []
        sem_data[key].append(r)
        
    semesters = []
    all_approved_courses = [] # To track all results for CGPA calculation
    
    for key, items in sem_data.items():
        session, semester = key.split("-")
        s_units = sum(i.get("course_units", 0) for i in items)
        s_points = sum(i.get("course_units", 0) * i.get("grade_point", 0.0) for i in items)
        all_approved_courses.extend(items)
        
        semesters.append(SemesterGPA(
            session=session,
            semester=semester,
            level=items[0].get("level", 100),
            total_units=s_units,
            total_points=s_points,
            gpa=round(s_points / s_units, 2) if s_units > 0 else 0.0,
            results=items  # Changed from 'courses' to 'results' to fix frontend crash
        ))

    # Calculate CGPA using best result per course (ESUT Standard)
    best_results = {}
    for r in all_approved_courses:
        code = r["course_code"]
        if code not in best_results or r.get("grade_point", 0) > best_results[code].get("grade_point", 0):
            best_results[code] = r
            
    total_units_attempted = sum(r.get("course_units", 0) for r in best_results.values())
    total_points_earned = sum(r.get("course_units", 0) * r.get("grade_point", 0.0) for r in best_results.values())
    
    cgpa = round(total_points_earned / total_units_attempted, 2) if total_units_attempted > 0 else 0.0
    
    # Fetch programme name – guard against missing programme_id
    prog = None
    try:
        if student.get("programme_id"):
            prog = await db.programmes.find_one({"_id": ObjectId(student["programme_id"])})
    except Exception as e:
        # Log the error internally (omitted here) and continue with None
        prog = None
    
    return AcademicSummary(
        student={
            "id": str(student["_id"]),
            "matric_number": student["matric_number"],
            "full_name": student["full_name"],
            "email": student["email"],
        "programme_id": student.get("programme_id"),
            "programme_name": prog["name"] if prog else "Unknown",
            "level": student["level"],
            "entry_year": student["entry_year"],
            "gender": student["gender"],
            "created_at": student["created_at"]
        },
        semesters=sorted(semesters, key=lambda x: (x.session, x.semester)),
        cgpa=cgpa,
        total_units_attempted=total_units_attempted,
        degree_class=get_degree_classification(cgpa)
    )

@router.patch("/{result_id}/approve")
async def approve_result(result_id: str, current_user: dict = Depends(require_admin)):
    db = get_database()
    res = await db.results.update_one(
        {"_id": ObjectId(result_id)},
        {"$set": {"status": "approved", "updated_at": datetime.utcnow()}}
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"message": "Result approved"}

@router.patch("/{result_id}/reject")
async def reject_result(result_id: str, reason: str, current_user: dict = Depends(require_admin)):
    db = get_database()
    res = await db.results.update_one(
        {"_id": ObjectId(result_id)},
        {"$set": {
            "status": "rejected", 
            "rejection_reason": reason,
            "updated_at": datetime.utcnow()
        }}
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"message": "Result rejected"}

@router.post("/approve-bulk")
async def bulk_approve_results(data: Dict[str, List[str]], current_user: dict = Depends(require_admin)):
    db = get_database()
    result_ids = [ObjectId(rid) for rid in data.get("result_ids", [])]
    
    res = await db.results.update_many(
        {"_id": {"$in": result_ids}},
        {"$set": {"status": "approved", "updated_at": datetime.utcnow()}}
    )
    return {"message": f"Successfully approved {res.modified_count} results"}

@router.get("/lecturer/{lecturer_id}")
async def get_lecturer_submissions(
    lecturer_id: str, 
    session: Optional[str] = Query(None),
    current_user: dict = Depends(require_lecturer)
):
    db = get_database()
    
    # 1. Fetch all courses assigned to this lecturer
    # This ensures that even courses with no results yet show up in the table
    course_query = {"lecturer_id": lecturer_id}
    if session:
        course_query["session"] = session
    assigned_courses = await db.courses.find(course_query).to_list(100)
    
    # 2. Aggregate results to show as "submissions" (grouped by course/session/semester)
    result_match = {"$or": [{"lecturer_id": lecturer_id}, {"uploaded_by": lecturer_id}]}
    if session:
        result_match["session"] = session

    pipeline = [
        {"$match": result_match},
        {"$group": {
            "_id": {"course": "$course_id", "session": "$session", "semester": "$semester"},
            "entry_count": {"$sum": 1},
            "status": {"$first": "$status"},
            "created_at": {"$max": "$created_at"}
        }}
    ]
    
    cursor = db.results.aggregate(pipeline)
    submission_map = {}
    async for doc in cursor:
        # Build lookup key: courseId_session_semester
        key = f"{doc['_id']['course']}_{doc['_id']['session']}_{doc['_id']['semester']}"
        submission_map[key] = doc

    submissions = []
    processed_keys: Set[str] = set()
    
    # 3. Build unified list starting with assigned courses
    for course in assigned_courses:
        cid = str(course["_id"])
        sess = course.get("session", "N/A")
        sem = course.get("semester", "N/A")
        key = f"{cid}_{sess}_{sem}"
        processed_keys.add(key)
        
        stats = submission_map.get(key)
        submissions.append({
            "id": key.replace("/", "-"),
            "course_code": course.get("code"),
            "course_title": course.get("title"),
            "session": sess,
            "semester": sem,
            "status": stats["status"] if stats else "Not Uploaded",
            "entry_count": stats["entry_count"] if stats else 0,
            "created_at": stats["created_at"] if stats else course.get("updated_at")
        })

    # 4. Add any submissions that exist for courses not currently assigned (historical)
    # Only do this if not filtering by session to keep the dashboard clean
    if not session:
        for key, doc in submission_map.items():
            if key in processed_keys:
                continue
            
            course_obj = await db.courses.find_one({"_id": ObjectId(doc["_id"]["course"])})
            submissions.append({
                "id": key.replace("/", "-"),
                "course_code": course_obj.get("code") if course_obj else "N/A",
                "course_title": course_obj.get("title") if course_obj else "Unknown",
                "session": doc["_id"]["session"],
                "semester": doc["_id"]["semester"],
                "status": doc["status"],
                "entry_count": doc["entry_count"],
                "created_at": doc["created_at"]
            })

    # Sort by creation date (descending)
    return {"submissions": sorted(submissions, key=lambda x: x["created_at"] or datetime.min, reverse=True)}