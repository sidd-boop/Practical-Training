from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import grading
from .database import Base, engine, get_db
from .models import Student
from .schemas import StudentCreate, StudentOut, StudentUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Student Grade Calculator", lifespan=lifespan)


def to_out(s: Student) -> StudentOut:
    """Final score and grade are computed on read, so they always match current weights."""
    score = grading.calculate_final_score(s.test1, s.test2, s.midsem, s.endsem)
    return StudentOut(
        roll_number=s.roll_number,
        name=s.name,
        test1=s.test1,
        test2=s.test2,
        midsem=s.midsem,
        endsem=s.endsem,
        final_score=score,
        grade=grading.assign_grade(score),
    )


def get_or_404(db: Session, roll_number: str) -> Student:
    student = db.scalar(select(Student).where(Student.roll_number == roll_number))
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Student '{roll_number}' not found")
    return student


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    return {
        "weights": {
            "tests (avg of test1 & test2)": grading.WEIGHT_TESTS,
            "midsem": grading.WEIGHT_MIDSEM,
            "endsem": grading.WEIGHT_ENDSEM,
        },
        "grade_scale": [{"min_score": m, "grade": g} for m, g in grading.GRADE_SCALE],
    }


@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Roll number '{payload.roll_number}' already exists"
        )
    db.refresh(student)
    return to_out(student)


@app.get("/students", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    students = db.scalars(select(Student).order_by(Student.roll_number)).all()
    return [to_out(s) for s in students]


@app.get("/students/{roll_number}", response_model=StudentOut)
def read_student(roll_number: str, db: Session = Depends(get_db)):
    return to_out(get_or_404(db, roll_number))


@app.put("/students/{roll_number}", response_model=StudentOut)
def update_student(roll_number: str, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = get_or_404(db, roll_number)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return to_out(student)


@app.delete("/students/{roll_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(roll_number: str, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, roll_number))
    db.commit()