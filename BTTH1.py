from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="API Quản lý Khóa học")

courses = [
    {"id": 1, "code": "PY101", "name": "Python Basic", "duration": 30, "fee": 3000000},
    {"id": 2, "code": "API101", "name": "FastAPI Basic", "duration": 24, "fee": 2500000},
    {"id": 3, "code": "JV101", "name": "Java Basic", "duration": 40, "fee": 4000000},
]

class CourseBase(BaseModel):
    code: str
    name: str
    duration: int = Field(gt=0)
    fee: int = Field(ge=0)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Mã không được để trống")
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Tên không được để trống")
        return value.strip()

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    pass

class CourseOut(CourseBase):
    id: int

def find_course_by_id(course_id: int):
    for course in courses:
        if course["id"] == course_id:
            return course
    return None

def is_code_exists(code: str, exclude_id: int | None = None) -> bool:
    normalized_code = code.strip().upper()
    for course in courses:
        if course["code"] == normalized_code and course["id"] != exclude_id:
            return True
    return False

@app.get("/courses", response_model=List[CourseOut])
def get_courses(
    keyword: str | None = Query(default=None, description="Tìm kiếm theo tên hoặc mã khóa học"),
    min_fee: int | None = Query(default=None, ge=0, description="Học phí tối thiểu"),
    max_fee: int | None = Query(default=None, ge=0, description="Học phí tối đa"),
):
    result = courses

    if keyword:
        keyword = keyword.strip().lower()
        result = [
            course
            for course in result
            if keyword in course["name"].lower() or keyword in course["code"].lower()
        ]

    if min_fee is not None:
        result = [course for course in result if course["fee"] >= min_fee]

    if max_fee is not None:
        result = [course for course in result if course["fee"] <= max_fee]

    return result

@app.get("/courses/{course_id}", response_model=CourseOut)
def get_course_detail(course_id: int):
    course = find_course_by_id(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
    return course

@app.post("/courses", response_model=CourseOut, status_code=201)
def create_course(course: CourseCreate):
    if is_code_exists(course.code):
        raise HTTPException(status_code=400, detail="Mã khóa học đã tồn tại")

    new_course = {
        "id": max((item["id"] for item in courses), default=0) + 1,
        "code": course.code,
        "name": course.name,
        "duration": course.duration,
        "fee": course.fee,
    }
    courses.append(new_course)
    return new_course

@app.put("/courses/{course_id}", response_model=CourseOut)
def update_course(course_id: int, course: CourseUpdate):
    existing_course = find_course_by_id(course_id)
    if existing_course is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")

    if is_code_exists(course.code, exclude_id=course_id):
        raise HTTPException(status_code=400, detail="Mã khóa học đã tồn tại")

    existing_course.update(
        {
            "code": course.code,
            "name": course.name,
            "duration": course.duration,
            "fee": course.fee,
        }
    )
    return existing_course

@app.delete("/courses/{course_id}")
def delete_course(course_id: int):
    for index, course in enumerate(courses):
        if course["id"] == course_id:
            del courses[index]
            return {"message": "Khóa học đã dược xóa thành công"}

    raise HTTPException(status_code=404, detail="Khóa học không tồn tại")
