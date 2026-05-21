"""
Seed script to populate the database with sample data.
Run: python seed.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
from bson import ObjectId

MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "esut_results_db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


PROGRAMMES = [
    {
        "name": "Bachelor of Science in Computer Science",
        "code": "BSC-CS",
        "faculty": "Faculty of Natural Sciences",
        "department": "Computer Science",
        "duration_years": 4,
        "description": "A rigorous programme covering algorithms, software engineering, AI, and systems.",
    },
    {
        "name": "Bachelor of Science in Mathematics",
        "code": "BSC-MTH",
        "faculty": "Faculty of Natural Sciences",
        "department": "Mathematics",
        "duration_years": 4,
        "description": "Pure and applied mathematics with focus on analysis and computation.",
    },
    {
        "name": "Bachelor of Engineering in Electrical Engineering",
        "code": "BEng-EE",
        "faculty": "Faculty of Engineering",
        "department": "Electrical Engineering",
        "duration_years": 5,
        "description": "Covers power systems, electronics, control systems, and telecommunications.",
    },
]

GRADING = [
    {"min_score": 70, "max_score": 100, "grade": "A", "grade_point": 5.0, "remark": "Excellent"},
    {"min_score": 60, "max_score": 69.99, "grade": "B", "grade_point": 4.0, "remark": "Very Good"},
    {"min_score": 50, "max_score": 59.99, "grade": "C", "grade_point": 3.0, "remark": "Good"},
    {"min_score": 45, "max_score": 49.99, "grade": "D", "grade_point": 2.0, "remark": "Pass"},
    {"min_score": 40, "max_score": 44.99, "grade": "E", "grade_point": 1.0, "remark": "Fail"},
    {"min_score": 0, "max_score": 39.99, "grade": "F", "grade_point": 0.0, "remark": "Fail"},
]


async def seed():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]

    print("🌱 Seeding database...")

    # Clear existing data
    for collection in ["users", "programmes", "courses", "students", "results", "grading_configs", "audit_logs"]:
        await db[collection].drop()

    # ── Programmes ───────────────────────────────────────────
    prog_ids = {}
    for prog in PROGRAMMES:
        prog["created_at"] = datetime.utcnow()
        prog["updated_at"] = datetime.utcnow()
        result = await db.programmes.insert_one(prog)
        prog_ids[prog["code"]] = result.inserted_id
        print(f"  ✅ Programme: {prog['name']}")

    # ── Global grading config ────────────────────────────────
    await db.grading_configs.insert_one({
        "programme_id": None,
        "grades": GRADING,
        "created_at": datetime.utcnow(),
    })
    print("  ✅ Grading config (global)")

    # ── Users (Admin + Lecturers) ────────────────────────────
    admin_id = (await db.users.insert_one({
        "email": "admin@esut.edu.ng",
        "full_name": "System Administrator",
        "role": "admin",
        "password_hash": pwd_context.hash("admin123"),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })).inserted_id
    print("  ✅ Admin: admin@esut.edu.ng / admin123")

    lecturers = [
        {"email": "dr.okafor@esut.edu.ng", "full_name": "Dr. Emeka Okafor", "staff_id": "ESUT/STAFF/001"},
        {"email": "prof.eze@esut.edu.ng", "full_name": "Prof. Chioma Eze", "staff_id": "ESUT/STAFF/002"},
        {"email": "dr.nwosu@esut.edu.ng", "full_name": "Dr. Kelechi Nwosu", "staff_id": "ESUT/STAFF/003"},
    ]
    lecturer_ids = []
    for lect in lecturers:
        lid = (await db.users.insert_one({
            **lect,
            "role": "lecturer",
            "password_hash": pwd_context.hash("lecturer123"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })).inserted_id
        lecturer_ids.append(lid)
        print(f"  ✅ Lecturer: {lect['email']} / lecturer123")

    # ── Courses for BSc Computer Science ────────────────────
    cs_prog_id = str(prog_ids["BSC-CS"])
    cs_courses = [
        # 100L First Semester
        {"code": "CSC101", "title": "Introduction to Computer Science", "units": 3, "semester": "first", "level": 100},
        {"code": "CSC103", "title": "Computer Programming I", "units": 3, "semester": "first", "level": 100},
        {"code": "MTH101", "title": "Elementary Mathematics I", "units": 3, "semester": "first", "level": 100},
        {"code": "PHY101", "title": "General Physics I", "units": 3, "semester": "first", "level": 100},
        {"code": "GST101", "title": "Use of English I", "units": 2, "semester": "first", "level": 100},
        # 100L Second Semester
        {"code": "CSC102", "title": "Computer Programming II", "units": 3, "semester": "second", "level": 100},
        {"code": "CSC104", "title": "Digital Logic Design", "units": 3, "semester": "second", "level": 100},
        {"code": "MTH102", "title": "Elementary Mathematics II", "units": 3, "semester": "second", "level": 100},
        {"code": "PHY102", "title": "General Physics II", "units": 3, "semester": "second", "level": 100},
        {"code": "GST102", "title": "Use of English II", "units": 2, "semester": "second", "level": 100},
        # 200L First Semester
        {"code": "CSC201", "title": "Data Structures and Algorithms", "units": 3, "semester": "first", "level": 200},
        {"code": "CSC203", "title": "Discrete Mathematics", "units": 3, "semester": "first", "level": 200},
        {"code": "CSC205", "title": "Computer Architecture", "units": 3, "semester": "first", "level": 200},
        {"code": "MTH201", "title": "Mathematical Methods I", "units": 3, "semester": "first", "level": 200},
        {"code": "STA201", "title": "Probability Theory", "units": 3, "semester": "first", "level": 200},
        # 200L Second Semester
        {"code": "CSC202", "title": "Object-Oriented Programming", "units": 3, "semester": "second", "level": 200},
        {"code": "CSC204", "title": "Operating Systems", "units": 3, "semester": "second", "level": 200},
        {"code": "CSC206", "title": "Database Systems I", "units": 3, "semester": "second", "level": 200},
        {"code": "MTH202", "title": "Mathematical Methods II", "units": 3, "semester": "second", "level": 200},
        {"code": "STA202", "title": "Statistics for Computing", "units": 2, "semester": "second", "level": 200},
    ]
    course_ids = []
    for course in cs_courses:
        course["programme_id"] = cs_prog_id
        course["is_elective"] = False
        course["created_at"] = datetime.utcnow()
        course["updated_at"] = datetime.utcnow()
        cid = (await db.courses.insert_one(course)).inserted_id
        course_ids.append(cid)

    print(f"  ✅ {len(cs_courses)} courses for BSc Computer Science")

    # ── Students ─────────────────────────────────────────────
    students_data = [
        {"matric_number": "ESUT/2021/CS/001", "full_name": "Chukwuemeka Obiora", "email": "emeka.obiora@student.esut.edu.ng", "gender": "Male", "entry_year": 2021, "level": 200},
        {"matric_number": "ESUT/2021/CS/002", "full_name": "Adaeze Nwosu", "email": "adaeze.nwosu@student.esut.edu.ng", "gender": "Female", "entry_year": 2021, "level": 200},
        {"matric_number": "ESUT/2021/CS/003", "full_name": "Ikechukwu Eze", "email": "ike.eze@student.esut.edu.ng", "gender": "Male", "entry_year": 2021, "level": 200},
        {"matric_number": "ESUT/2021/CS/004", "full_name": "Ngozi Okafor", "email": "ngozi.okafor@student.esut.edu.ng", "gender": "Female", "entry_year": 2021, "level": 200},
        {"matric_number": "ESUT/2021/CS/005", "full_name": "Chidi Ugwu", "email": "chidi.ugwu@student.esut.edu.ng", "gender": "Male", "entry_year": 2021, "level": 200},
        {"matric_number": "ESUT/2022/CS/001", "full_name": "Amaka Ifeanyi", "email": "amaka.ifeanyi@student.esut.edu.ng", "gender": "Female", "entry_year": 2022, "level": 100},
        {"matric_number": "ESUT/2022/CS/002", "full_name": "Obinna Obi", "email": "obinna.obi@student.esut.edu.ng", "gender": "Male", "entry_year": 2022, "level": 100},
    ]

    student_ids = []
    for s in students_data:
        s["programme_id"] = cs_prog_id
        s["created_at"] = datetime.utcnow()
        s["updated_at"] = datetime.utcnow()
        sid = (await db.students.insert_one(s)).inserted_id
        student_ids.append(sid)

        # Create student user account
        await db.users.insert_one({
            "email": s["email"],
            "full_name": s["full_name"],
            "role": "student",
            "password_hash": pwd_context.hash(s["matric_number"]),
            "matric_number": s["matric_number"],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

    print(f"  ✅ {len(students_data)} students created")

    # ── Results for 100L students ────────────────────────────
    import random

    def get_grade(score):
        if score >= 70: return "A", 5.0
        elif score >= 60: return "B", 4.0
        elif score >= 50: return "C", 3.0
        elif score >= 45: return "D", 2.0
        elif score >= 40: return "E", 1.0
        return "F", 0.0

    # 100L First Semester courses (first 5)
    first_sem_100 = [c for c in await db.courses.find({"level": 100, "semester": "first"}).to_list(10)]
    second_sem_100 = [c for c in await db.courses.find({"level": 100, "semester": "second"}).to_list(10)]

    # Seed results for 200L students (who completed 100L)
    score_profiles = {
        str(student_ids[0]): (70, 95),  # First class student
        str(student_ids[1]): (60, 80),  # 2:1 student
        str(student_ids[2]): (50, 70),  # 2:2 student
        str(student_ids[3]): (55, 75),
        str(student_ids[4]): (45, 65),
    }

    result_count = 0
    for sid, (low, high) in score_profiles.items():
        for course in first_sem_100:
            score = round(random.uniform(low, high), 1)
            grade, gp = get_grade(score)
            await db.results.insert_one({
                "student_id": sid,
                "course_id": str(course["_id"]),
                "score": score,
                "grade": grade,
                "grade_point": gp,
                "session": "2021/2022",
                "semester": "first",
                "status": "approved",
                "lecturer_id": str(lecturer_ids[0]),
                "uploaded_by": str(lecturer_ids[0]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            result_count += 1

        for course in second_sem_100:
            score = round(random.uniform(low, high), 1)
            grade, gp = get_grade(score)
            await db.results.insert_one({
                "student_id": sid,
                "course_id": str(course["_id"]),
                "score": score,
                "grade": grade,
                "grade_point": gp,
                "session": "2021/2022",
                "semester": "second",
                "status": "approved",
                "lecturer_id": str(lecturer_ids[0]),
                "uploaded_by": str(lecturer_ids[0]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            result_count += 1

    # Pending results
    pending_courses = first_sem_100[:3]
    new_students = [student_ids[5], student_ids[6]]
    for sid in new_students:
        for course in pending_courses:
            score = round(random.uniform(50, 90), 1)
            grade, gp = get_grade(score)
            await db.results.insert_one({
                "student_id": str(sid),
                "course_id": str(course["_id"]),
                "score": score,
                "grade": grade,
                "grade_point": gp,
                "session": "2022/2023",
                "semester": "first",
                "status": "pending",
                "uploaded_by": str(lecturer_ids[1]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            result_count += 1

    print(f"  ✅ {result_count} results seeded")

    # ── Create indexes ────────────────────────────────────────
    await db.users.create_index("email", unique=True)
    await db.students.create_index("matric_number", unique=True)
    await db.courses.create_index("code", unique=True)
    await db.results.create_index(
        [("student_id", 1), ("course_id", 1), ("session", 1), ("semester", 1)], unique=True
    )

    print("\n🎉 Seeding complete!")
    print("\n📋 Login Credentials:")
    print("  Admin:    admin@esut.edu.ng        / admin123")
    print("  Lecturer: dr.okafor@esut.edu.ng    / lecturer123")
    print("  Student:  emeka.obiora@student.esut.edu.ng / ESUT/2021/CS/001")
    print("\n🚀 Start the server: uvicorn app.main:app --reload")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
