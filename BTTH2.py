import re
from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="API Quản lý học viên")

students = [
    {"id": 1, "code": "SV001", "name": "Nguyen Van A", "email": "a@gmail.com", "age": 20},
    {"id": 2, "code": "SV002", "name": "Tran Thi B", "email": "b@gmail.com", "age": 22},
    {"id": 3, "code": "SV003", "name": "Le Van C", "email": "c@gmail.com", "age": 18},
]

class StudentBase(BaseModel):
    code: str
    name: str
    email: str
    age: int = Field(gt=0)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Mã học viên không được để trống")
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Tên học viên không được để trống")
        return value.strip().title()

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip()
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if value is None or not value.strip():
            raise ValueError("Email không được để trống")

        if not re.match(pattern, email):
            raise ValueError("Email không hợp lệ")

        return email

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Tuổi học viên phải lớn hơn 0")
        return value

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int

def find_student_by_id(student_id: int):
    for student in students:
        if student["id"] == student_id:
            return student
    return None

def is_code_exists(code: str, exclude_id: int | None = None) -> bool:
    normalized_code = code.strip().upper()
    for student in students:
        if student["code"] == normalized_code and student["id"] != exclude_id:
            return True
    return False

@app.get("/students", response_model=List[StudentOut])
def get_students(
    keyword: str | None = Query(default=None, description="Tìm theo tên, mã hoặc email"),
    min_age: int | None = Query(default=None, ge=0, description="Tuổi tối thiểu"),
    max_age: int | None = Query(default=None, ge=0, description="Tuổi tối đa"),
):
    result = students

    if keyword:
        keyword = keyword.strip().lower()
        result = [
            student
            for student in result
            if keyword in student["name"].lower()
            or keyword in student["code"].lower()
            or keyword in student["email"].lower()
        ]

    if min_age is not None:
        result = [student for student in result if student["age"] >= min_age]

    if max_age is not None:
        result = [student for student in result if student["age"] <= max_age]

    return result

@app.get("/students/{student_id}", response_model=StudentOut)
def get_student_detail(student_id: int):
    student = find_student_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.post("/students", response_model=StudentOut, status_code=201)
def create_student(student: StudentCreate):
    if is_code_exists(student.code):
        raise HTTPException(status_code=400, detail="Mã học viên đã tồn tại")

    new_student = {
        "id": max((item["id"] for item in students), default=0) + 1,
        "code": student.code,
        "name": student.name,
        "email": student.email,
        "age": student.age,
    }
    students.append(new_student)
    return new_student

@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, student: StudentUpdate):
    existing_student = find_student_by_id(student_id)
    if existing_student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    if is_code_exists(student.code, exclude_id=student_id):
        raise HTTPException(status_code=400, detail="Mã học viên đã tồn tại")

    existing_student.update(
        {
            "code": student.code,
            "name": student.name,
            "email": student.email,
            "age": student.age,
        }
    )
    return existing_student

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    for index, student in enumerate(students):
        if student["id"] == student_id:
            del students[index]
            return {"message": "Học viên đã được xóa thành công"}

    raise HTTPException(status_code=404, detail="Student not found")
