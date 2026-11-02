
"""Weights and grade boundaries. Edit here (or via env vars) to change the policy."""
import os

# Maximum marks for each assessment
TEST_MAX = 10
MIDSEM_MAX = 50
ENDSEM_MAX = 100

# Tests weight applies to the AVERAGE of Test 1 and Test 2.
WEIGHT_TESTS = float(os.getenv("WEIGHT_TESTS", "0.20"))
WEIGHT_MIDSEM = float(os.getenv("WEIGHT_MIDSEM", "0.30"))
WEIGHT_ENDSEM = float(os.getenv("WEIGHT_ENDSEM", "0.50"))

if abs((WEIGHT_TESTS + WEIGHT_MIDSEM + WEIGHT_ENDSEM) - 1.0) > 1e-9:
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
    test1: float,
    test2: float,
    midsem: float,
    endsem: float
) -> float:

    # Normalize all components to a scale of 100
    tests_avg = ((test1 + test2) / 2) / TEST_MAX * 100
    midsem_normalized = (midsem / MIDSEM_MAX) * 100
    endsem_normalized = (endsem / ENDSEM_MAX) * 100

    score = (
        tests_avg * WEIGHT_TESTS
        + midsem_normalized * WEIGHT_MIDSEM
        + endsem_normalized * WEIGHT_ENDSEM
    )

    return round(score, 2)


def assign_grade(score: float) -> str:
    for minimum, grade in GRADE_SCALE:
        if score >= minimum:
            return grade
    return "F"
