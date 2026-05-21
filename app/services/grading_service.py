from typing import List, Dict, Optional, Tuple
from app.database import get_database


DEFAULT_GRADING_SYSTEM = [
    {"min_score": 70, "max_score": 100, "grade": "A", "grade_point": 5.0, "remark": "Excellent"},
    {"min_score": 60, "max_score": 69.99, "grade": "B", "grade_point": 4.0, "remark": "Very Good"},
    {"min_score": 50, "max_score": 59.99, "grade": "C", "grade_point": 3.0, "remark": "Good"},
    {"min_score": 45, "max_score": 49.99, "grade": "D", "grade_point": 2.0, "remark": "Pass"},
    {"min_score": 40, "max_score": 44.99, "grade": "E", "grade_point": 1.0, "remark": "Fail"},
    {"min_score": 0, "max_score": 39.99, "grade": "F", "grade_point": 0.0, "remark": "Fail"},
]


async def get_grading_system(programme_id: Optional[str] = None) -> List[dict]:
    db = get_database()
    
    if programme_id:
        config = await db.grading_configs.find_one({"programme_id": programme_id})
        if config:
            return config["grades"]
    
    # Fall back to global config
    global_config = await db.grading_configs.find_one({"programme_id": None})
    if global_config:
        return global_config["grades"]
    
    return DEFAULT_GRADING_SYSTEM


def calculate_grade(score: float, grading_system: List[dict]) -> Tuple[str, float, str]:
    """Returns (grade, grade_point, remark)"""
    for grade_config in sorted(grading_system, key=lambda x: x["min_score"], reverse=True):
        if grade_config["min_score"] <= score <= grade_config["max_score"]:
            return grade_config["grade"], grade_config["grade_point"], grade_config["remark"]
    return "F", 0.0, "Fail"


def calculate_gpa(results: List[Dict]) -> Tuple[float, int, float]:
    """
    Returns (gpa, total_units, total_quality_points)
    """
    total_units = 0
    total_quality_points = 0.0
    
    for result in results:
        units = result.get("course_units", 0)
        grade_point = result.get("grade_point", 0.0)
        total_units += units
        total_quality_points += units * grade_point
    
    if total_units == 0:
        return 0.0, 0, 0.0
    
    gpa = round(total_quality_points / total_units, 2)
    return gpa, total_units, total_quality_points


def calculate_cgpa(semester_results: List[List[Dict]]) -> Tuple[float, int]:
    """
    Calculate CGPA across all semesters.
    Handles retakes: uses highest score.
    Returns (cgpa, total_units)
    """
    # Aggregate best results per course
    best_results: Dict[str, Dict] = {}
    
    for semester in semester_results:
        for result in semester:
            course_id = result["course_id"]
            if course_id not in best_results:
                best_results[course_id] = result
            else:
                # Keep highest grade point
                if result.get("grade_point", 0) > best_results[course_id].get("grade_point", 0):
                    best_results[course_id] = result
    
    all_results = list(best_results.values())
    cgpa, total_units, _ = calculate_gpa(all_results)
    return cgpa, total_units


def get_degree_classification(cgpa: float) -> str:
    if cgpa >= 4.50:
        return "First Class Honours"
    elif cgpa >= 3.50:
        return "Second Class Honours (Upper Division)"
    elif cgpa >= 2.40:
        return "Second Class Honours (Lower Division)"
    elif cgpa >= 1.50:
        return "Third Class Honours"
    elif cgpa >= 1.00:
        return "Pass"
    else:
        return "Fail"


async def get_student_academic_summary(student_id: str, programme_id: str) -> Dict:
    """Full academic summary for a student"""
    db = get_database()
    grading_system = await get_grading_system(programme_id)
    
    pipeline = [
        {"$match": {"student_id": student_id, "status": "approved"}},
        {"$lookup": {
            "from": "courses",
            "localField": "course_id",
            "foreignField": "_id_str",
            "as": "course"
        }},
        {"$sort": {"session": 1, "semester": 1}}
    ]
    
    results = await db.results.find(
        {"student_id": student_id, "status": "approved"}
    ).to_list(1000)
    
    # Group by session + semester
    semester_map: Dict[str, List] = {}
    
    for result in results:
        key = f"{result['session']}_{result['semester']}"
        if key not in semester_map:
            semester_map[key] = []
        semester_map[key].append(result)
    
    semesters = []
    for key, sem_results in semester_map.items():
        session, semester = key.rsplit("_", 1)
        gpa, units, points = calculate_gpa(sem_results)
        semesters.append({
            "session": session,
            "semester": semester,
            "gpa": gpa,
            "total_units": units,
            "results": sem_results
        })
    
    all_semester_results = [s["results"] for s in semesters]
    cgpa, total_units = calculate_cgpa(all_semester_results)
    degree_class = get_degree_classification(cgpa)
    
    return {
        "semesters": semesters,
        "cgpa": cgpa,
        "total_units": total_units,
        "degree_class": degree_class
    }
