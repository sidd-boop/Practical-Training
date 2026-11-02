from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Mark = Field(ge=0, le=100, description="Marks out of 100")


class StudentCreate(BaseModel):
    roll_number: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    test1: float = Mark
    test2: float = Mark
    midsem: float = Mark
    endsem: float = Mark

    @field_validator("roll_number", "name")
    @classmethod
    def strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    test1: Optional[float] = Field(default=None, ge=0, le=100)
    test2: Optional[float] = Field(default=None, ge=0, le=100)
    midsem: Optional[float] = Field(default=None, ge=0, le=100)
    endsem: Optional[float] = Field(default=None, ge=0, le=100)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roll_number: str
    name: str
    test1: float
    test2: float
    midsem: float
    endsem: float
    final_score: float
    grade: str