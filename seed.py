"""
Comprehensive ESUT (Enugu State University of Science and Technology) Seed Script
Populates:
1. Global & Postgraduate Grading Configurations
2. Comprehensive Faculties, Departments & Programmes across ESUT:
   - Faculty of Engineering (M.Eng Computer Eng, B.Eng Computer Eng, B.Eng Electrical, M.Eng Electrical, B.Eng Mechanical, B.Eng Civil, B.Eng Chemical)
   - Faculty of Applied Natural Sciences (B.Sc Computer Science, M.Sc Computer Science, B.Sc Mathematics, B.Sc Biochemistry, B.Sc Microbiology)
   - Faculty of Management Sciences (B.Sc Business Admin, MBA, B.Sc Accountancy, B.Sc Banking & Finance)
   - Faculty of Environmental Sciences (B.Sc Architecture, B.Sc Estate Management)
   - Faculty of Law (LL.B Law)
   - Faculty of Basic Medical / Health Sciences (B.N.Sc Nursing Science, BMLS Medical Lab Science)
3. Faculty Members & Departmental Lecturers:
   - Specified Computer Engineering Masters Lecturers: Dr. Gide, Dr. Oleka C. V., Dr. Chagunye T., Dr. Nduanya, Dr. Nzeribe
   - Lecturers across other faculties and departments
4. Masters in Computer Engineering (M.Eng) Course Allocation:
   - First Semester: CEE 810, CEE 831, CEE 823, CEE 851
   - Second Semester: CEE 872, CEE 874, CEE 816, CEE 818
   - Third Semester: CEE 870, CEE 871, CEE 873, CEE 879
   - Plus courses across undergraduate and other postgraduate departments
5. 2024/2025 Class List for External Defence (13 students with Reg Nos):
   - All 13 candidates with registered student records, student user accounts,
     and approved results across 1st, 2nd, and 3rd semesters ready for external defence.
6. Additional undergraduate and postgraduate students with academic records across multiple faculties.
"""
import asyncio
from datetime import datetime
import random
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import dotenv_values
import os
import sys

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.dirname(__file__))
from app.utils.auth import hash_password

# Load environment
env_path = os.path.join(os.path.dirname(__file__), ".env")
env_vars = dotenv_values(env_path) if os.path.exists(env_path) else {}
MONGODB_URL = env_vars.get("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = env_vars.get("DATABASE_NAME", "esut_results_db")

# ─────────────────────────────────────────────────────────────
# 1. PROGRAMMES
# ─────────────────────────────────────────────────────────────
FACULTIES_AND_PROGRAMMES = [
    # Faculty of Engineering
    {
        "name": "Masters in Engineering (Computer Engineering)",
        "code": "MENG-CPE",
        "faculty": "Faculty of Engineering",
        "department": "Computer Engineering",
        "duration_years": 2,
        "description": "Postgraduate Masters degree in Computer Engineering specializing in intelligent systems, robotics, advanced embedded systems, and security.",
    },
    {
        "name": "B.Eng Computer Engineering",
        "code": "COE",
        "faculty": "Faculty of Engineering",
        "department": "Computer Engineering",
        "duration_years": 5,
        "description": "Undergraduate professional engineering programme covering computer architecture, hardware-software integration, and robotics.",
    },
    {
        "name": "B.Eng Electrical & Electronics Engineering",
        "code": "EEE",
        "faculty": "Faculty of Engineering",
        "department": "Electrical & Electronics Engineering",
        "duration_years": 5,
        "description": "Undergraduate programme focusing on power systems, telecommunications, instrumentation, and control.",
    },
    {
        "name": "Masters in Engineering (Electrical & Electronics Engineering)",
        "code": "MENG-EEE",
        "faculty": "Faculty of Engineering",
        "department": "Electrical & Electronics Engineering",
        "duration_years": 2,
        "description": "Postgraduate programme in advanced electrical power networks, telecommunications, and high-voltage engineering.",
    },
    {
        "name": "B.Eng Mechanical & Production Engineering",
        "code": "MEE",
        "faculty": "Faculty of Engineering",
        "department": "Mechanical Engineering",
        "duration_years": 5,
        "description": "Covers thermodynamics, fluid mechanics, CAD/CAM, machine design, and production management.",
    },
    {
        "name": "B.Eng Civil Engineering",
        "code": "CVE",
        "faculty": "Faculty of Engineering",
        "department": "Civil Engineering",
        "duration_years": 5,
        "description": "Structural engineering, geotechnical engineering, hydraulics, and highway transportation.",
    },
    {
        "name": "B.Eng Chemical Engineering",
        "code": "CHE",
        "faculty": "Faculty of Engineering",
        "department": "Chemical Engineering",
        "duration_years": 5,
        "description": "Process engineering, reaction kinetics, petrochemicals, and separation processes.",
    },

    # Faculty of Applied Natural Sciences / Computing
    {
        "name": "Bachelor of Science in Computer Science",
        "code": "CSC",
        "faculty": "Faculty of Applied Natural Sciences",
        "department": "Computer Science",
        "duration_years": 4,
        "description": "Core computing algorithms, AI, cloud computing, and software development.",
    },
    {
        "name": "Master of Science in Computer Science",
        "code": "MSC-CSC",
        "faculty": "Faculty of Applied Natural Sciences",
        "department": "Computer Science",
        "duration_years": 2,
        "description": "Advanced research in artificial intelligence, cybersecurity, and distributed systems.",
    },
    {
        "name": "Bachelor of Science in Mathematics",
        "code": "BSC-MTH",
        "faculty": "Faculty of Applied Natural Sciences",
        "department": "Mathematics & Statistics",
        "duration_years": 4,
        "description": "Applied and pure mathematical modeling, numerical analysis, and statistics.",
    },
    {
        "name": "Bachelor of Science in Biochemistry",
        "code": "BCH",
        "faculty": "Faculty of Applied Natural Sciences",
        "department": "Biochemistry",
        "duration_years": 4,
        "description": "Enzymology, molecular genetics, clinical biochemistry, and pharmacology.",
    },
    {
        "name": "Bachelor of Science in Microbiology",
        "code": "MCB",
        "faculty": "Faculty of Applied Natural Sciences",
        "department": "Microbiology",
        "duration_years": 4,
        "description": "Medical, industrial, environmental, and food microbiology.",
    },

    # Faculty of Management Sciences
    {
        "name": "Bachelor of Science in Business Administration",
        "code": "BUS",
        "faculty": "Faculty of Management Sciences",
        "department": "Business Administration",
        "duration_years": 4,
        "description": "Strategic management, organizational behavior, marketing, and entrepreneurship.",
    },
    {
        "name": "Master of Business Administration (MBA)",
        "code": "MBA",
        "faculty": "Faculty of Management Sciences",
        "department": "Business Administration",
        "duration_years": 2,
        "description": "Executive business leadership, finance, corporate strategy, and operations.",
    },
    {
        "name": "Bachelor of Science in Accountancy",
        "code": "ACC",
        "faculty": "Faculty of Management Sciences",
        "department": "Accountancy",
        "duration_years": 4,
        "description": "Financial accounting, taxation, auditing, and corporate governance.",
    },
    {
        "name": "Bachelor of Science in Banking & Finance",
        "code": "BAF",
        "faculty": "Faculty of Management Sciences",
        "department": "Banking & Finance",
        "duration_years": 4,
        "description": "Financial institutions, risk management, capital markets, and investments.",
    },

    # Faculty of Environmental Sciences
    {
        "name": "Bachelor of Science in Architecture",
        "code": "ARC",
        "faculty": "Faculty of Environmental Sciences",
        "department": "Architecture",
        "duration_years": 4,
        "description": "Architectural design, urban planning, building science, and sustainable structures.",
    },
    {
        "name": "Bachelor of Science in Estate Management",
        "code": "ESM",
        "faculty": "Faculty of Environmental Sciences",
        "department": "Estate Management",
        "duration_years": 4,
        "description": "Property valuation, real estate appraisal, land economy, and property development.",
    },

    # Faculty of Law
    {
        "name": "Bachelor of Laws (LL.B)",
        "code": "LLB",
        "faculty": "Faculty of Law",
        "department": "Law",
        "duration_years": 5,
        "description": "Constitutional law, commercial law, criminal jurisprudence, and international law.",
    },

    # Faculty of Basic Medical Sciences / Health Sciences
    {
        "name": "Bachelor of Nursing Science (B.N.Sc)",
        "code": "BNS",
        "faculty": "Faculty of Basic Medical Sciences",
        "department": "Nursing Science",
        "duration_years": 5,
        "description": "Clinical nursing, community health, maternal and child healthcare.",
    },
    {
        "name": "Bachelor of Medical Laboratory Science (BMLS)",
        "code": "BMLS",
        "faculty": "Faculty of Basic Medical Sciences",
        "department": "Medical Laboratory Science",
        "duration_years": 5,
        "description": "Histopathology, medical hematology, chemical pathology, and medical microbiology.",
    },
]

# ─────────────────────────────────────────────────────────────
# 2. GRADING CONFIG
# ─────────────────────────────────────────────────────────────
GLOBAL_GRADING = [
    {"min_score": 70, "max_score": 100, "grade": "A", "grade_point": 5.0, "remark": "Excellent"},
    {"min_score": 60, "max_score": 69.99, "grade": "B", "grade_point": 4.0, "remark": "Very Good"},
    {"min_score": 50, "max_score": 59.99, "grade": "C", "grade_point": 3.0, "remark": "Good"},
    {"min_score": 45, "max_score": 49.99, "grade": "D", "grade_point": 2.0, "remark": "Pass"},
    {"min_score": 40, "max_score": 44.99, "grade": "E", "grade_point": 1.0, "remark": "Fail"},
    {"min_score": 0, "max_score": 39.99, "grade": "F", "grade_point": 0.0, "remark": "Fail"},
]

def compute_grade(score: float):
    if score >= 70.0:
        return "A", 5.0
    elif score >= 60.0:
        return "B", 4.0
    elif score >= 50.0:
        return "C", 3.0
    elif score >= 45.0:
        return "D", 2.0
    elif score >= 40.0:
        return "E", 1.0
    else:
        return "F", 0.0

# ─────────────────────────────────────────────────────────────
# 3. LECTURERS (including specified M.Eng Computer Engineering faculty)
# ─────────────────────────────────────────────────────────────
LECTURERS = [
    # M.Eng Computer Engineering Lecturers requested
    {"email": "dr.gide@esut.edu.ng", "full_name": "Dr. Gide", "staff_id": "ESUT/ENG/CPE/001", "department": "Computer Engineering"},
    {"email": "dr.oleka@esut.edu.ng", "full_name": "Dr. Oleka, C. V", "staff_id": "ESUT/ENG/CPE/002", "department": "Computer Engineering"},
    {"email": "dr.chagunye@esut.edu.ng", "full_name": "Dr. Chagunye, T", "staff_id": "ESUT/ENG/CPE/003", "department": "Computer Engineering"},
    {"email": "dr.nduanya@esut.edu.ng", "full_name": "Dr. Nduanya", "staff_id": "ESUT/ENG/CPE/004", "department": "Computer Engineering"},
    {"email": "dr.nzeribe@esut.edu.ng", "full_name": "Dr. Nzeribe", "staff_id": "ESUT/ENG/CPE/005", "department": "Computer Engineering"},

    # Other Engineering Lecturers
    {"email": "prof.nwangwu@esut.edu.ng", "full_name": "Prof. E. C. Nwangwu", "staff_id": "ESUT/ENG/EEE/001", "department": "Electrical & Electronics Engineering"},
    {"email": "dr.agbo@esut.edu.ng", "full_name": "Engr. Dr. O. S. Agbo", "staff_id": "ESUT/ENG/MEE/001", "department": "Mechanical Engineering"},
    {"email": "dr.onah@esut.edu.ng", "full_name": "Engr. Dr. K. C. Onah", "staff_id": "ESUT/ENG/CVE/001", "department": "Civil Engineering"},
    {"email": "prof.aneke@esut.edu.ng", "full_name": "Prof. B. O. Aneke", "staff_id": "ESUT/ENG/CHE/001", "department": "Chemical Engineering"},

    # Computer Science & Natural Sciences Lecturers
    {"email": "dr.okafor@esut.edu.ng", "full_name": "Dr. Emeka Okafor", "staff_id": "ESUT/SCI/CSC/001", "department": "Computer Science"},
    {"email": "prof.eze@esut.edu.ng", "full_name": "Prof. Chioma Eze", "staff_id": "ESUT/SCI/CSC/002", "department": "Computer Science"},
    {"email": "dr.nwosu@esut.edu.ng", "full_name": "Dr. Kelechi Nwosu", "staff_id": "ESUT/SCI/MTH/001", "department": "Mathematics & Statistics"},
    {"email": "dr.ugwuanyi@esut.edu.ng", "full_name": "Dr. J. O. Ugwuanyi", "staff_id": "ESUT/SCI/BCH/001", "department": "Biochemistry"},
    {"email": "dr.anioke@esut.edu.ng", "full_name": "Dr. (Mrs) N. Anioke", "staff_id": "ESUT/SCI/MCB/001", "department": "Microbiology"},

    # Management Sciences Lecturers
    {"email": "prof.udeh@esut.edu.ng", "full_name": "Prof. F. C. Udeh", "staff_id": "ESUT/MGT/BUS/001", "department": "Business Administration"},
    {"email": "dr.anike@esut.edu.ng", "full_name": "Dr. (Mrs) N. P. Anike", "staff_id": "ESUT/MGT/ACC/001", "department": "Accountancy"},
    {"email": "dr.igwe@esut.edu.ng", "full_name": "Dr. N. N. Igwe", "staff_id": "ESUT/MGT/BAF/001", "department": "Banking & Finance"},

    # Environmental Sciences, Law & Medicine
    {"email": "dr.ani@esut.edu.ng", "full_name": "Arc. Dr. Anthony Ani", "staff_id": "ESUT/ENV/ARC/001", "department": "Architecture"},
    {"email": "dr.okoye@esut.edu.ng", "full_name": "Barr. Dr. I. J. Okoye", "staff_id": "ESUT/LAW/001", "department": "Law"},
    {"email": "dr.eneh@esut.edu.ng", "full_name": "Dr. Chinedu Eneh", "staff_id": "ESUT/MED/NUR/001", "department": "Nursing Science"},
]

# ─────────────────────────────────────────────────────────────
# 4. MASTERS 2024/2025 CLASS LIST FOR EXTERNAL DEFENCE
# ─────────────────────────────────────────────────────────────
MENG_DEFENCE_STUDENTS = [
    {"sn": 1, "name": "Akpata Adaeze Florence", "reg_no": "2024070000978", "gender": "Female", "profile": "distinction"},
    {"sn": 2, "name": "Eneota Remigius Obinna", "reg_no": "2024070000592", "gender": "Male", "profile": "upper_credit"},
    {"sn": 3, "name": "Ngwu Sunday Ikechukwu", "reg_no": "2024070000644", "gender": "Male", "profile": "distinction"},
    {"sn": 4, "name": "Nnadi Kingsley Ifeanyi", "reg_no": "2024070001355", "gender": "Male", "profile": "upper_credit"},
    {"sn": 5, "name": "Odezulu Justice Chukwuebuka", "reg_no": "2024070001334", "gender": "Male", "profile": "distinction"},
    {"sn": 6, "name": "Ogbonna Emmanuel", "reg_no": "2024070001017", "gender": "Male", "profile": "distinction"},
    {"sn": 7, "name": "Okorie Godwin Ikechukwu", "reg_no": "2024070001412", "gender": "Male", "profile": "distinction"},
    {"sn": 8, "name": "Edemejaro Kesiena", "reg_no": "2024070001291", "gender": "Male", "profile": "upper_credit"},
    {"sn": 9, "name": "Ogbuagu Samuel Chinedu", "reg_no": "2024070000953", "gender": "Male", "profile": "upper_credit"},
    {"sn": 10, "name": "Olisa Raphael Emmanuel", "reg_no": "2024070000681", "gender": "Male", "profile": "distinction"},
    {"sn": 11, "name": "Onyegbule Theodore Okwudili", "reg_no": "2024070000773", "gender": "Male", "profile": "upper_credit"},
    {"sn": 12, "name": "Ozoagu Franklin Chukwuanugo", "reg_no": "2024070000059", "gender": "Male", "profile": "distinction"},
    {"sn": 13, "name": "Ugama Ifeanyi Ongele", "reg_no": "2024070001149", "gender": "Male", "profile": "upper_credit"},
]

# ─────────────────────────────────────────────────────────────
# 5. M.ENG COURSE ALLOCATION
# ─────────────────────────────────────────────────────────────
MENG_COURSES = [
    # FIRST SEMESTER
    {"code": "CEE 810", "title": "ADVANCE ENGINEERING MATHEMATICS", "units": 3, "semester": "first", "level": 800, "lecturer_key": "dr.gide@esut.edu.ng"},
    {"code": "CEE 831", "title": "SYSTEM MODELLING & SIMULATION", "units": 3, "semester": "first", "level": 800, "lecturer_key": "dr.gide@esut.edu.ng"},
    {"code": "CEE 823", "title": "CRYPTOGRAPHY/COMPUTER NETWORK SECURITY & MANAGEMENT", "units": 3, "semester": "first", "level": 800, "lecturer_key": "dr.oleka@esut.edu.ng"},
    {"code": "CEE 851", "title": "MODERN CONTROL THEORY", "units": 3, "semester": "first", "level": 800, "lecturer_key": "dr.chagunye@esut.edu.ng"},

    # SECOND SEMESTER
    {"code": "CEE 872", "title": "KNOWLEDGE-BASED EXPERT SYSTEMS AND WEB AGENTS", "units": 3, "semester": "second", "level": 800, "lecturer_key": "dr.nduanya@esut.edu.ng"},
    {"code": "CEE 874", "title": "DESIGN AND ANALYSIS OF ROBOTICS SYSTEM CONTROL", "units": 3, "semester": "second", "level": 800, "lecturer_key": "dr.oleka@esut.edu.ng"},
    {"code": "CEE 816", "title": "ADVANCED EMBEDDED SYSTEM ENGINEERING", "units": 3, "semester": "second", "level": 800, "lecturer_key": "dr.nzeribe@esut.edu.ng"},
    {"code": "CEE 818", "title": "DIGITAL IMAGE PROCESSING & NEURAL NETWORK", "units": 3, "semester": "second", "level": 800, "lecturer_key": "dr.gide@esut.edu.ng"},

    # THIRD SEMESTER
    {"code": "CEE 870", "title": "INTELLIGENT SYSTEMS ENGINEERING", "units": 3, "semester": "third", "level": 800, "lecturer_key": "dr.nduanya@esut.edu.ng"},
    {"code": "CEE 871", "title": "ADVANCE REAL-TIME AND COMPUTING SYSTEM", "units": 3, "semester": "third", "level": 800, "lecturer_key": "dr.chagunye@esut.edu.ng"},
    {"code": "CEE 873", "title": "WIRELESS & MOBILE COMMUNICATION", "units": 3, "semester": "third", "level": 800, "lecturer_key": "dr.chagunye@esut.edu.ng"},
    {"code": "CEE 879", "title": "INTELLIGENT DATABASE MANAGEMENT SYSTEM", "units": 3, "semester": "third", "level": 800, "lecturer_key": "dr.chagunye@esut.edu.ng"},
]

# ─────────────────────────────────────────────────────────────
# 6. COURSES FOR OTHER PROGRAMMES
# ─────────────────────────────────────────────────────────────
OTHER_PROGRAMME_COURSES = {
    # B.Eng Computer Engineering
    "COE": [
        {"code": "COE 101", "title": "Introduction to Computer Engineering", "units": 2, "semester": "first", "level": 100, "lecturer_key": "dr.gide@esut.edu.ng"},
        {"code": "COE 102", "title": "Introduction to Computers", "units": 2, "semester": "second", "level": 100, "lecturer_key": "dr.gide@esut.edu.ng"},
        {"code": "COE 201", "title": "Computer Programming for Engineers (C++)", "units": 3, "semester": "first", "level": 200, "lecturer_key": "dr.nduanya@esut.edu.ng"},
        {"code": "COE 202", "title": "Electrical Circuits & Measurements", "units": 3, "semester": "second", "level": 200, "lecturer_key": "dr.oleka@esut.edu.ng"},
        {"code": "COE 312", "title": "Digital Logic Gates & Switching Theory", "units": 3, "semester": "second", "level": 300, "lecturer_key": "dr.nzeribe@esut.edu.ng"},
        {"code": "COE 401", "title": "Digital Signal Processing", "units": 3, "semester": "first", "level": 400, "lecturer_key": "dr.gide@esut.edu.ng"},
        {"code": "COE 501", "title": "Microprocessor Systems & Interfacing", "units": 3, "semester": "first", "level": 500, "lecturer_key": "dr.nzeribe@esut.edu.ng"},
        {"code": "COE 502", "title": "Artificial Intelligence in Engineering", "units": 3, "semester": "second", "level": 500, "lecturer_key": "dr.chagunye@esut.edu.ng"},
    ],
    # B.Eng Electrical Engineering
    "EEE": [
        {"code": "EEE 151", "title": "Principles of Electronics", "units": 3, "semester": "first", "level": 100, "lecturer_key": "prof.nwangwu@esut.edu.ng"},
        {"code": "EEE 201", "title": "Applied Electricity I", "units": 3, "semester": "first", "level": 200, "lecturer_key": "prof.nwangwu@esut.edu.ng"},
        {"code": "EEE 311", "title": "Electric Power Systems I", "units": 3, "semester": "first", "level": 300, "lecturer_key": "prof.nwangwu@esut.edu.ng"},
        {"code": "EEE 421", "title": "Telecommunication Engineering", "units": 3, "semester": "first", "level": 400, "lecturer_key": "prof.nwangwu@esut.edu.ng"},
        {"code": "EEE 511", "title": "Power System Analysis & Control", "units": 3, "semester": "first", "level": 500, "lecturer_key": "prof.nwangwu@esut.edu.ng"},
    ],
    # B.Sc Computer Science
    "CSC": [
        {"code": "CSC 101", "title": "Introduction to Computer Science", "units": 3, "semester": "first", "level": 100, "lecturer_key": "dr.okafor@esut.edu.ng"},
        {"code": "CSC 102", "title": "Computer Programming I (Python)", "units": 3, "semester": "second", "level": 100, "lecturer_key": "dr.okafor@esut.edu.ng"},
        {"code": "CSC 201", "title": "Data Structures & Algorithms", "units": 3, "semester": "first", "level": 200, "lecturer_key": "prof.eze@esut.edu.ng"},
        {"code": "CSC 202", "title": "Object-Oriented Programming (Java)", "units": 3, "semester": "second", "level": 200, "lecturer_key": "prof.eze@esut.edu.ng"},
        {"code": "CSC 301", "title": "Database Design & Management", "units": 3, "semester": "first", "level": 300, "lecturer_key": "prof.eze@esut.edu.ng"},
        {"code": "CSC 401", "title": "Software Engineering Principles", "units": 3, "semester": "first", "level": 400, "lecturer_key": "dr.okafor@esut.edu.ng"},
    ],
    # B.Eng Mechanical Engineering
    "MEE": [
        {"code": "MEE 201", "title": "Engineering Thermodynamics I", "units": 3, "semester": "first", "level": 200, "lecturer_key": "dr.agbo@esut.edu.ng"},
        {"code": "MEE 301", "title": "Mechanics of Deformable Bodies", "units": 3, "semester": "first", "level": 300, "lecturer_key": "dr.agbo@esut.edu.ng"},
        {"code": "MEE 401", "title": "Fluid Dynamics & Turbomachinery", "units": 3, "semester": "first", "level": 400, "lecturer_key": "dr.agbo@esut.edu.ng"},
        {"code": "MEE 501", "title": "Design of Mechanical Systems", "units": 3, "semester": "first", "level": 500, "lecturer_key": "dr.agbo@esut.edu.ng"},
    ],
    # B.Eng Civil Engineering
    "CVE": [
        {"code": "CVE 201", "title": "Civil Engineering Materials", "units": 3, "semester": "first", "level": 200, "lecturer_key": "dr.onah@esut.edu.ng"},
        {"code": "CVE 301", "title": "Theory of Structures I", "units": 3, "semester": "first", "level": 300, "lecturer_key": "dr.onah@esut.edu.ng"},
        {"code": "CVE 401", "title": "Geotechnical & Soil Mechanics", "units": 3, "semester": "first", "level": 400, "lecturer_key": "dr.onah@esut.edu.ng"},
        {"code": "CVE 501", "title": "Design of Reinforced Concrete Structures", "units": 3, "semester": "first", "level": 500, "lecturer_key": "dr.onah@esut.edu.ng"},
    ],
    # B.Sc Accountancy
    "ACC": [
        {"code": "ACC 101", "title": "Principles of Accounting I", "units": 3, "semester": "first", "level": 100, "lecturer_key": "dr.anike@esut.edu.ng"},
        {"code": "ACC 201", "title": "Financial Accounting I", "units": 3, "semester": "first", "level": 200, "lecturer_key": "dr.anike@esut.edu.ng"},
        {"code": "ACC 301", "title": "Auditing Principles & Investigation", "units": 3, "semester": "first", "level": 300, "lecturer_key": "dr.anike@esut.edu.ng"},
        {"code": "ACC 401", "title": "Advanced Taxation & Fiscal Policy", "units": 3, "semester": "first", "level": 400, "lecturer_key": "dr.anike@esut.edu.ng"},
    ],
    # B.Sc Business Administration
    "BUS": [
        {"code": "BUS 101", "title": "Introduction to Business Management", "units": 3, "semester": "first", "level": 100, "lecturer_key": "prof.udeh@esut.edu.ng"},
        {"code": "BUS 201", "title": "Principles of Management", "units": 3, "semester": "first", "level": 200, "lecturer_key": "prof.udeh@esut.edu.ng"},
        {"code": "BUS 301", "title": "Operations & Production Management", "units": 3, "semester": "first", "level": 300, "lecturer_key": "prof.udeh@esut.edu.ng"},
        {"code": "BUS 401", "title": "Business Policy & Strategic Management", "units": 3, "semester": "first", "level": 400, "lecturer_key": "prof.udeh@esut.edu.ng"},
    ],
    # LL.B Law
    "LLB": [
        {"code": "LAW 101", "title": "Legal Method I", "units": 3, "semester": "first", "level": 100, "lecturer_key": "dr.okoye@esut.edu.ng"},
        {"code": "LAW 201", "title": "Nigerian Constitutional Law I", "units": 4, "semester": "first", "level": 200, "lecturer_key": "dr.okoye@esut.edu.ng"},
        {"code": "LAW 301", "title": "Criminal Law & Procedure I", "units": 4, "semester": "first", "level": 300, "lecturer_key": "dr.okoye@esut.edu.ng"},
        {"code": "LAW 401", "title": "Commercial & Corporate Law", "units": 4, "semester": "first", "level": 400, "lecturer_key": "dr.okoye@esut.edu.ng"},
    ],
    # B.N.Sc Nursing Science
    "BNS": [
        {"code": "NSC 201", "title": "Foundation of Professional Nursing", "units": 3, "semester": "first", "level": 200, "lecturer_key": "dr.eneh@esut.edu.ng"},
        {"code": "NSC 301", "title": "Medical-Surgical Nursing I", "units": 4, "semester": "first", "level": 300, "lecturer_key": "dr.eneh@esut.edu.ng"},
        {"code": "NSC 401", "title": "Maternal and Child Health Nursing", "units": 4, "semester": "first", "level": 400, "lecturer_key": "dr.eneh@esut.edu.ng"},
    ],
}

# ─────────────────────────────────────────────────────────────
# 7. ADDITIONAL STUDENTS ACROSS DEPARTMENTS
# ─────────────────────────────────────────────────────────────
OTHER_DEPT_STUDENTS = [
    # B.Eng Computer Engineering
    {"name": "Nnamani Chukwuemeka Godswill", "reg_no": "ESUT/2021/COE/012", "dept_code": "COE", "gender": "Male", "level": 400, "entry_year": 2021},
    {"name": "Ibeabuchi Cynthia Chisom", "reg_no": "ESUT/2022/COE/034", "dept_code": "COE", "gender": "Female", "level": 300, "entry_year": 2022},
    {"name": "Ezeilo Kelvin Somtochukwu", "reg_no": "ESUT/2023/COE/056", "dept_code": "COE", "gender": "Male", "level": 200, "entry_year": 2023},
    
    # B.Eng Electrical & Electronics
    {"name": "Onyia Kenechukwu Paul", "reg_no": "ESUT/2021/EEE/008", "dept_code": "EEE", "gender": "Male", "level": 400, "entry_year": 2021},
    {"name": "Umeh Jennifer Oluebube", "reg_no": "ESUT/2022/EEE/019", "dept_code": "EEE", "gender": "Female", "level": 300, "entry_year": 2022},
    
    # B.Sc Computer Science
    {"name": "Chukwuemeka Obiora Jude", "reg_no": "ESUT/2021/CSC/001", "dept_code": "CSC", "gender": "Male", "level": 400, "entry_year": 2021},
    {"name": "Anigbo Blessing Ngozi", "reg_no": "ESUT/2022/CSC/042", "dept_code": "CSC", "gender": "Female", "level": 300, "entry_year": 2022},
    
    # B.Eng Mechanical Engineering
    {"name": "Offor Anthony Chidera", "reg_no": "ESUT/2021/MEE/015", "dept_code": "MEE", "gender": "Male", "level": 400, "entry_year": 2021},
    
    # B.Eng Civil Engineering
    {"name": "Mbah Stanley Chinonso", "reg_no": "ESUT/2021/CVE/022", "dept_code": "CVE", "gender": "Male", "level": 400, "entry_year": 2021},
    
    # B.Sc Accountancy
    {"name": "Ani Chinaza Peace", "reg_no": "ESUT/2022/ACC/011", "dept_code": "ACC", "gender": "Female", "level": 300, "entry_year": 2022},
    
    # B.Sc Business Administration
    {"name": "Okafor Paschal Chinedu", "reg_no": "ESUT/2021/BUS/044", "dept_code": "BUS", "gender": "Male", "level": 400, "entry_year": 2021},
    
    # LL.B Law
    {"name": "Nwigwe Favour Chinemerem", "reg_no": "ESUT/2021/LAW/007", "dept_code": "LLB", "gender": "Female", "level": 400, "entry_year": 2021},
    
    # B.N.Sc Nursing Science
    {"name": "Edeh Miracle Amarachi", "reg_no": "ESUT/2021/BNS/018", "dept_code": "BNS", "gender": "Female", "level": 400, "entry_year": 2021},
]

# ─────────────────────────────────────────────────────────────
# SEED RUNNER
# ─────────────────────────────────────────────────────────────
async def seed_esut():
    print(f"Connecting to MongoDB at: {MONGODB_URL[:35]}... (DB: {DB_NAME})")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]

    print("\n🏛️  STARTING ESUT DATABASE SEEDING...")

    # 1. Ensure Global Grading Config
    await db.grading_configs.update_one(
        {"programme_id": None},
        {"$set": {"grades": GLOBAL_GRADING, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    print("  ✅ Global Grading Configuration seeded (A to F scale)")

    # 2. Seed Admin User
    admin_hash = hash_password("admin123")
    await db.users.update_one(
        {"email": "admin@esut.edu.ng"},
        {"$set": {
            "full_name": "System Administrator",
            "role": "admin",
            "password_hash": admin_hash,
            "is_active": True,
            "staff_id": "ESUT/ADMIN/001",
            "updated_at": datetime.utcnow()
        },
        "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True
    )
    print("  ✅ Admin user verified: admin@esut.edu.ng / admin123")

    # 3. Seed Faculties & Programmes
    prog_map = {} # code -> ObjectId
    for prog_data in FACULTIES_AND_PROGRAMMES:
        code = prog_data["code"]
        existing = await db.programmes.find_one({"code": code})
        if existing:
            await db.programmes.update_one(
                {"_id": existing["_id"]},
                {"$set": {**prog_data, "updated_at": datetime.utcnow()}}
            )
            prog_map[code] = existing["_id"]
        else:
            doc = {**prog_data, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            res = await db.programmes.insert_one(doc)
            prog_map[code] = res.inserted_id
        print(f"  ✅ Programme: [{code}] {prog_data['name']} ({prog_data['faculty']})")

    # 4. Seed Lecturers
    lecturer_map = {} # email -> ObjectId
    lect_hash = hash_password("lecturer123")
    for l in LECTURERS:
        email = l["email"]
        existing = await db.users.find_one({"email": email})
        user_doc = {
            "full_name": l["full_name"],
            "role": "lecturer",
            "staff_id": l["staff_id"],
            "is_active": True,
            "department": l.get("department", ""),
            "updated_at": datetime.utcnow()
        }
        if existing:
            await db.users.update_one({"_id": existing["_id"]}, {"$set": user_doc})
            lecturer_map[email] = existing["_id"]
        else:
            user_doc.update({
                "email": email,
                "password_hash": lect_hash,
                "created_at": datetime.utcnow()
            })
            res = await db.users.insert_one(user_doc)
            lecturer_map[email] = res.inserted_id
        print(f"  ✅ Lecturer: {l['full_name']} ({l['staff_id']}) -> {email}")

    # 5. Seed M.Eng Computer Engineering Courses
    meng_cpe_id = prog_map["MENG-CPE"]
    course_map = {} # code -> ObjectId
    session = "2024/2025"

    for c in MENG_COURSES:
        code = c["code"]
        lect_id = lecturer_map.get(c["lecturer_key"])
        c_doc = {
            "code": code,
            "title": c["title"],
            "units": c["units"],
            "semester": c["semester"],
            "level": c["level"],
            "programme_code": "MENG-CPE",
            "programme_id": str(meng_cpe_id),
            "is_elective": False,
            "lecturer_id": str(lect_id) if lect_id else None,
            "session": session,
            "updated_at": datetime.utcnow()
        }
        existing = await db.courses.find_one({"code": code})
        if existing:
            await db.courses.update_one({"_id": existing["_id"]}, {"$set": c_doc})
            course_map[code] = existing["_id"]
        else:
            c_doc["created_at"] = datetime.utcnow()
            res = await db.courses.insert_one(c_doc)
            course_map[code] = res.inserted_id
        print(f"  ✅ M.Eng Course: {code} - {c['title']} ({c['semester'].title()} Sem) -> {c['lecturer_key']}")

    # 6. Seed Courses for Other Programmes
    for p_code, courses in OTHER_PROGRAMME_COURSES.items():
        p_id = prog_map.get(p_code)
        for c in courses:
            code = c["code"]
            lect_id = lecturer_map.get(c["lecturer_key"])
            c_doc = {
                "code": code,
                "title": c["title"],
                "units": c["units"],
                "semester": c["semester"],
                "level": c["level"],
                "programme_code": p_code,
                "programme_id": str(p_id) if p_id else None,
                "is_elective": False,
                "lecturer_id": str(lect_id) if lect_id else None,
                "session": session,
                "updated_at": datetime.utcnow()
            }
            existing = await db.courses.find_one({"code": code})
            if existing:
                await db.courses.update_one({"_id": existing["_id"]}, {"$set": c_doc})
                course_map[code] = existing["_id"]
            else:
                c_doc["created_at"] = datetime.utcnow()
                res = await db.courses.insert_one(c_doc)
                course_map[code] = res.inserted_id

    print(f"  ✅ Total courses registered in database: {len(course_map)}")

    # 7. Seed M.Eng Computer Engineering 2024/2025 Class List for External Defence
    print("\n🎓 SEEDING MASTERS 2024/2025 CLASS LIST FOR EXTERNAL DEFENCE (13 CANDIDATES)...")
    
    # Define score profiles so results are realistic and distinction-grade for defence
    profile_score_ranges = {
        "distinction": (73.0, 89.5),   # Straight A's with occasional high B
        "upper_credit": (64.0, 81.0),  # A's and B's
    }

    # Deterministic pseudo-random seed so repeated runs give consistent, high quality transcripts
    rng = random.Random(202407)

    meng_student_ids = []
    total_defence_results = 0

    for item in MENG_DEFENCE_STUDENTS:
        reg_no = item["reg_no"]
        name = item["name"]
        gender = item["gender"]
        # Generate official postgraduate student email
        clean_name = name.lower().replace(",", "").split()
        first_name = clean_name[1] if len(clean_name) > 1 else clean_name[0]
        last_name = clean_name[0]
        email = f"{first_name}.{last_name}@pg.esut.edu.ng"

        # Student user account
        user_hash = hash_password(reg_no)
        user_doc = {
            "email": email,
            "full_name": name,
            "role": "student",
            "matric_number": reg_no,
            "is_active": True,
            "updated_at": datetime.utcnow()
        }
        existing_user = await db.users.find_one({"matric_number": reg_no})
        if existing_user:
            await db.users.update_one({"_id": existing_user["_id"]}, {"$set": user_doc})
            user_id = existing_user["_id"]
        else:
            user_doc.update({"password_hash": user_hash, "created_at": datetime.utcnow()})
            res_u = await db.users.insert_one(user_doc)
            user_id = res_u.inserted_id

        # Student profile doc
        student_doc = {
            "matric_number": reg_no,
            "full_name": name,
            "email": email,
            "programme_id": str(meng_cpe_id),
            "level": 800,
            "entry_year": 2024,
            "gender": gender,
            "phone": f"+234803{rng.randint(1000000, 9999999)}",
            "updated_at": datetime.utcnow()
        }
        existing_s = await db.students.find_one({"matric_number": reg_no})
        if existing_s:
            await db.students.update_one({"_id": existing_s["_id"]}, {"$set": student_doc})
            sid = existing_s["_id"]
        else:
            student_doc["created_at"] = datetime.utcnow()
            res_s = await db.students.insert_one(student_doc)
            sid = res_s.inserted_id

        meng_student_ids.append((sid, reg_no, name))

        # Seed approved results across all 12 courses (Semesters 1, 2, and 3)
        low, high = profile_score_ranges.get(item["profile"], (65.0, 85.0))
        for course_def in MENG_COURSES:
            c_code = course_def["code"]
            c_id = course_map[c_code]
            score = round(rng.uniform(low, high), 1)
            grade, gp = compute_grade(score)
            lect_id = lecturer_map.get(course_def["lecturer_key"])

            result_doc = {
                "student_id": str(sid),
                "matric_number": reg_no,
                "course_id": str(c_id),
                "course_code": c_code,
                "course_title": course_def["title"],
                "course_units": course_def["units"],
                "score": score,
                "grade": grade,
                "grade_point": gp,
                "points": gp,
                "session": "2024/2025",
                "semester": course_def["semester"],
                "status": "approved",
                "lecturer_id": str(lect_id) if lect_id else None,
                "uploaded_by": str(lect_id) if lect_id else str(user_id),
                "updated_at": datetime.utcnow()
            }
            # Upsert result to prevent duplicates
            await db.results.update_one(
                {
                    "matric_number": reg_no,
                    "course_code": c_code,
                    "session": "2024/2025",
                    "semester": course_def["semester"]
                },
                {"$set": result_doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            )
            total_defence_results += 1

        print(f"  Candidate #{item['sn']}: {name} (Reg: {reg_no}) -> 12 Courses Seeded (1st, 2nd, 3rd Semesters)")

    print(f"  ✅ Total defense candidate results seeded: {total_defence_results}")

    # 8. Seed Additional Students Across Other Departments
    print("\n👥 SEEDING STUDENTS AND RESULTS ACROSS OTHER DEPARTMENTS...")
    other_results_count = 0
    for s_info in OTHER_DEPT_STUDENTS:
        reg_no = s_info["reg_no"]
        name = s_info["name"]
        dept_code = s_info["dept_code"]
        p_id = prog_map.get(dept_code)
        gender = s_info["gender"]
        level = s_info["level"]
        entry_year = s_info["entry_year"]

        clean_name = name.lower().replace(",", "").split()
        email = f"{clean_name[1]}.{clean_name[0]}@student.esut.edu.ng"

        # User account
        user_doc = {
            "email": email,
            "full_name": name,
            "role": "student",
            "matric_number": reg_no,
            "is_active": True,
            "updated_at": datetime.utcnow()
        }
        ex_u = await db.users.find_one({"matric_number": reg_no})
        if ex_u:
            await db.users.update_one({"_id": ex_u["_id"]}, {"$set": user_doc})
            uid = ex_u["_id"]
        else:
            user_doc.update({"password_hash": hash_password(reg_no), "created_at": datetime.utcnow()})
            res_u = await db.users.insert_one(user_doc)
            uid = res_u.inserted_id

        # Student profile
        std_doc = {
            "matric_number": reg_no,
            "full_name": name,
            "email": email,
            "programme_id": str(p_id) if p_id else None,
            "level": level,
            "entry_year": entry_year,
            "gender": gender,
            "phone": f"+234810{rng.randint(1000000, 9999999)}",
            "updated_at": datetime.utcnow()
        }
        ex_s = await db.students.find_one({"matric_number": reg_no})
        if ex_s:
            await db.students.update_one({"_id": ex_s["_id"]}, {"$set": std_doc})
            sid = ex_s["_id"]
        else:
            std_doc["created_at"] = datetime.utcnow()
            res_s = await db.students.insert_one(std_doc)
            sid = res_s.inserted_id

        # Seed results for courses in their department
        dept_courses = OTHER_PROGRAMME_COURSES.get(dept_code, [])
        for c_def in dept_courses[:4]:
            c_code = c_def["code"]
            c_id = course_map.get(c_code)
            score = round(rng.uniform(55.0, 85.0), 1)
            grade, gp = compute_grade(score)
            lect_id = lecturer_map.get(c_def["lecturer_key"])

            res_doc = {
                "student_id": str(sid),
                "matric_number": reg_no,
                "course_id": str(c_id) if c_id else c_code,
                "course_code": c_code,
                "course_title": c_def["title"],
                "course_units": c_def["units"],
                "score": score,
                "grade": grade,
                "grade_point": gp,
                "points": gp,
                "session": "2024/2025",
                "semester": c_def["semester"],
                "status": "approved",
                "lecturer_id": str(lect_id) if lect_id else None,
                "uploaded_by": str(lect_id) if lect_id else str(uid),
                "updated_at": datetime.utcnow()
            }
            await db.results.update_one(
                {
                    "matric_number": reg_no,
                    "course_code": c_code,
                    "session": "2024/2025",
                    "semester": c_def["semester"]
                },
                {"$set": res_doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            )
            other_results_count += 1

        print(f"  ✅ Student: {name} ({reg_no}) - [{dept_code}] Level {level}")

    # 9. Set Current Session
    await db.current_sessions.update_one(
        {"programme_id": str(meng_cpe_id)},
        {"$set": {"session": "2024/2025", "updated_at": datetime.utcnow()}},
        upsert=True
    )
    await db.current_sessions.update_one(
        {"programme_id": None},
        {"$set": {"session": "2024/2025", "updated_at": datetime.utcnow()}},
        upsert=True
    )

    # 10. Ensure Indexes
    try:
        await db.users.create_index("email", unique=True)
        await db.students.create_index("matric_number", unique=True)
        await db.courses.create_index("code", unique=True)
        await db.results.create_index(
            [("matric_number", 1), ("course_code", 1), ("session", 1), ("semester", 1)],
            unique=True
        )
    except Exception as e:
        print(f"  ℹ️  Index check: {e}")

    # Summary
    student_count = await db.students.count_documents({})
    course_count = await db.courses.count_documents({})
    result_count = await db.results.count_documents({})
    user_count = await db.users.count_documents({})
    prog_count = await db.programmes.count_documents({})

    print("\n" + "="*70)
    print("🎉 ESUT DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"• Total Faculties & Programmes: {prog_count}")
    print(f"• Total System Users:          {user_count}")
    print(f"• Total Active Courses:        {course_count}")
    print(f"• Total Registered Students:   {student_count}")
    print(f"• Total Verified Results:      {result_count}")
    print("="*70)
    print("\n🔐 KEY LOGIN CREDENTIALS:")
    print("  System Admin:      admin@esut.edu.ng / admin123")
    print("  M.Eng Lecturer:    dr.gide@esut.edu.ng / lecturer123")
    print("  M.Eng Lecturer:    dr.oleka@esut.edu.ng / lecturer123")
    print("  M.Eng Lecturer:    dr.chagunye@esut.edu.ng / lecturer123")
    print("  M.Eng Lecturer:    dr.nduanya@esut.edu.ng / lecturer123")
    print("  M.Eng Lecturer:    dr.nzeribe@esut.edu.ng / lecturer123")
    print("  Defence Candidate: adaeze.akpata@pg.esut.edu.ng / 2024070000978")
    print("  Defence Candidate: emmanuel.ogbonna@pg.esut.edu.ng / 2024070001017")
    print("="*70)

    client.close()

if __name__ == "__main__":
    asyncio.run(seed_esut())
