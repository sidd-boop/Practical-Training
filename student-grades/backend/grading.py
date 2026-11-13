
"""Weights and grade boundaries. Edit here (or via env vars) to change the policy."""
import os

# Maximum marks for each assessment
QUIZ_MAX = 25
MIDSEM_MAX = 50
ENDSEM_MAX = 100

# Tests weight applies to the AVERAGE of Quiz 1 and Quiz 2.
WEIGHT_QUIZZES = float(os.getenv("WEIGHT_QUIZZES", "0.20"))
WEIGHT_MIDSEM = float(os.getenv("WEIGHT_MIDSEM", "0.30"))
WEIGHT_ENDSEM = float(os.getenv("WEIGHT_ENDSEM", "0.50"))

if abs((WEIGHT_QUIZZES + WEIGHT_MIDSEM + WEIGHT_ENDSEM) - 1.0) > 1e-9:
    raise ValueError("Weights must add up to 1.0")

GRADE_SCALE = [
    (80, "AA"),
    (70, "AB"),
    (60, "BB"),
    (50, "BC"),
    (40, "CC"),
    (30, "DD"),
    (0, "F"),
]


def calculate_final_score(
    quiz1: float,
    quiz2: float,
    midsem: float,
    endsem: float,
) -> float:

    # Normalize all components to a scale of 100
    quizzes_avg = ((quiz1 + quiz2) / 2) / QUIZ_MAX * 100
    midsem_normalized = (midsem / MIDSEM_MAX) * 100
    endsem_normalized = (endsem / ENDSEM_MAX) * 100

    score = (
        quizzes_avg * WEIGHT_QUIZZES
        + midsem_normalized * WEIGHT_MIDSEM
        + endsem_normalized * WEIGHT_ENDSEM
    )

    return round(score, 2)


def assign_grade(score: float) -> str:
    for minimum, grade in GRADE_SCALE:
        if score >= minimum:
            return grade
    return "F"
