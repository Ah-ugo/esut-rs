from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    LECTURER = "lecturer"
    STUDENT = "student"


class Semester(str, Enum):
    FIRST = "first"
    SECOND = "second"


class Level(int, Enum):
    L100 = 100
    L200 = 200
    L300 = 300
    L400 = 400
    L500 = 500


class ResultStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DegreeClass(str, Enum):
    FIRST_CLASS = "First Class Honours"
    SECOND_UPPER = "Second Class Honours (Upper Division)"
    SECOND_LOWER = "Second Class Honours (Lower Division)"
    THIRD_CLASS = "Third Class Honours"
    PASS = "Pass"
    FAIL = "Fail"


# ── User Schemas ──────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    matric_number: Optional[str] = None
    staff_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: str
    matric_number: Optional[str] = None
    staff_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Programme Schemas ──────────────────────────────────────
class ProgrammeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=20)
    faculty: str
    department: str
    duration_years: int = Field(..., ge=4, le=6)
    description: Optional[str] = None


class ProgrammeCreate(ProgrammeBase):
    pass


class ProgrammeOut(ProgrammeBase):
    id: str
    created_at: datetime
    total_students: Optional[int] = 0


# ── Course Schemas ──────────────────────────────────────────
class CourseBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=20)
    title: str = Field(..., min_length=3, max_length=200)
    units: int = Field(..., ge=1, le=6)
    semester: Semester
    level: int = Field(..., ge=100, le=500)
    programme_code: str # Changed from programme_id to use readable code
    is_elective: bool = False
    description: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseOut(CourseBase):
    id: str
    programme_name: Optional[str] = None
    created_at: datetime


class CourseAssignment(BaseModel):
    lecturer_id: str
    session: str  # e.g. "2023/2024"


# ── Student Schemas ──────────────────────────────────────────
class StudentBase(BaseModel):
    matric_number: str = Field(..., min_length=5, max_length=20)
    full_name: str
    email: EmailStr
    programme_id: str
    level: int = Field(..., ge=100, le=500)
    entry_year: int
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    date_of_birth: Optional[datetime] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentOut(StudentBase):
    id: str
    programme_name: Optional[str] = None
    cgpa: Optional[float] = None
    degree_class: Optional[str] = None
    created_at: datetime


# ── Result Schemas ──────────────────────────────────────────
class ResultCreate(BaseModel):
    matric_number: str # Changed from student_id
    course_code: str   # Changed from course_id
    score: float = Field(..., ge=0, le=100)
    session: str  # e.g. "2023/2024"
    semester: Semester

    @validator("score")
    def round_score(cls, v):
        return round(v, 2)


class BulkResultEntry(BaseModel):
    matric_number: str
    score: float = Field(..., ge=0, le=100)


class BulkResultUpload(BaseModel):
    course_code: str # Changed from course_id
    session: str
    semester: Semester
    results: List[BulkResultEntry]


class ResultOut(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    matric_number: Optional[str] = None
    course_id: str
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    course_units: Optional[int] = None
    score: float
    grade: str
    grade_point: float
    session: str
    semester: Semester
    status: ResultStatus
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── GPA Schemas ──────────────────────────────────────────
class SemesterGPA(BaseModel):
    session: str
    semester: Semester
    level: int
    total_units: int
    total_points: float
    gpa: float
    results: List[ResultOut]


class AcademicSummary(BaseModel):
    student: StudentOut
    semesters: List[SemesterGPA]
    cgpa: float
    total_units_attempted: int
    degree_class: DegreeClass


# ── Grading Config ──────────────────────────────────────────
class GradeConfig(BaseModel):
    min_score: float
    max_score: float
    grade: str
    grade_point: float
    remark: str


class GradingSystem(BaseModel):
    programme_id: Optional[str] = None  # None = global default
    grades: List[GradeConfig]


# ── Audit Log Schemas ──────────────────────────────────────────
class AuditLogOut(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime


# ── Pagination ──────────────────────────────────────────
class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int


# ── Dashboard Stats ──────────────────────────────────────────
class AdminStats(BaseModel):
    total_students: int
    total_lecturers: int
    total_courses: int
    total_programmes: int
    pending_results: int
    approved_results: int
    recent_uploads: List[Dict[str, Any]]
    gpa_distribution: Dict[str, int]
