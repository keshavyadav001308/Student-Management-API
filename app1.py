from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List
import json
import os

app = FastAPI(title="Student Management API")

DB_FILE = "students.json"


# --------------------------
# Utility Functions
# --------------------------

def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# --------------------------
# Pydantic Model
# --------------------------

class Student(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=3, max_length=50)
    age: int = Field(gt=5, lt=100)
    grade: str
    marks: List[int] = Field(min_items=1, max_items=10)

    average: float = 0

    # Validate marks between 0-100
    @field_validator("marks")
    @classmethod
    def validate_marks(cls, value):
        for mark in value:
            if mark < 0 or mark > 100:
                raise ValueError("Marks must be between 0 and 100")
        return value

    # Calculate average automatically
    @model_validator(mode="after")
    def calculate_average(self):
        self.average = round(sum(self.marks) / len(self.marks), 2)
        return self


# --------------------------
# GET - All Students
# --------------------------

@app.get("/students")
def get_students():
    return load_data()


# --------------------------
# GET - Single Student
# --------------------------

@app.get("/students/{student_id}")
def get_student(student_id: int):
    data = load_data()

    for student in data:
        if student["id"] == student_id:
            return student

    raise HTTPException(status_code=404, detail="Student not found")


# --------------------------
# POST - Add Student
# --------------------------

@app.post("/students")
def add_student(student: Student):
    data = load_data()

    # Check duplicate ID
    for existing in data:
        if existing["id"] == student.id:
            raise HTTPException(
                status_code=400,
                detail="Student ID already exists"
            )

    student_dict = student.model_dump()
    data.append(student_dict)
    save_data(data)

    return {
        "message": "Student added successfully",
        "data": student_dict
    }


# --------------------------
# PUT - Update Student
# --------------------------
from typing import Optional

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    grade: Optional[str] = None
    marks: Optional[List[int]] = None

@app.patch("/students/{student_id}")
def partial_update(student_id: int, student_update: StudentUpdate):
    data = load_data()

    for index, student in enumerate(data):
        if student["id"] == student_id:

            update_data = student_update.model_dump(exclude_unset=True)

            # Update only provided fields
            student.update(update_data)

            # 🔥 Recalculate average if marks updated
            if "marks" in update_data:
                student["average"] = round(
                    sum(student["marks"]) / len(student["marks"]), 2
                )

            data[index] = student
            save_data(data)

            return {"message": "Student partially updated", "data": student}

    raise HTTPException(status_code=404, detail="Student not found")



# --------------------------
# DELETE - Remove Student
# --------------------------

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    data = load_data()

    for student in data:
        if student["id"] == student_id:
            data.remove(student)
            save_data(data)
            return {"message": "Student deleted successfully"}

    raise HTTPException(status_code=404, detail="Student not found")
