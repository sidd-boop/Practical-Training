import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ROLL_NUMBER_PATTERN = re.compile(r"^\d{3}[A-Z]{2}\d{3}$")


class StudentCreate(BaseModel):
    roll_number: str = Field(min_length=1, max_length=50, description="e.g. 241DS030")
    name: str = Field(min_length=1, max_length=120, description="Letters and spaces only")
    quiz1: float = Field(ge=0, le=25, description="Marks out of 25")
    quiz2: float = Field(ge=0, le=25, description="Marks out of 25")
    midsem: float = Field(ge=0, le=50, description="Marks out of 50")
    endsem: float = Field(ge=0, le=100, description="Marks out of 100")

    @field_validator("roll_number")
    @classmethod
    def validate_roll_number(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("must not be blank")
        if not ROLL_NUMBER_PATTERN.match(v):
            raise ValueError(
                "Roll number must follow the pattern like 241DS030 "
                "(3 digits, 2 uppercase letters, 3 digits)"
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        if not re.match(r"^[A-Za-z][A-Za-z \-]*$", v):
            raise ValueError("Name must contain only letters, spaces, and hyphens")
        return v


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    quiz1: Optional[float] = Field(default=None, ge=0, le=25, description="Marks out of 25")
    quiz2: Optional[float] = Field(default=None, ge=0, le=25, description="Marks out of 25")
    midsem: Optional[float] = Field(default=None, ge=0, le=50, description="Marks out of 50")
    endsem: Optional[float] = Field(default=None, ge=0, le=100, description="Marks out of 100")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        if not re.match(r"^[A-Za-z][A-Za-z \-]*$", v):
            raise ValueError("Name must contain only letters, spaces, and hyphens")
        return v


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roll_number: str
    name: str
    quiz1: float
    quiz2: float
    midsem: float
    endsem: float
    final_score: float
    grade: str
