from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ExecutePayload(BaseModel):
    language: str
    code: str

class TestCase(BaseModel):
    id: str
    input: str
    expected_output: str
    is_sample: bool
    points: int = 0

class SubmissionResult(BaseModel):
    testcase_id: str
    passed: bool
    actual_output: str
    runtime_ms: int

class SubmissionResponse(BaseModel):
    passed: bool
    score: int
    results: List[SubmissionResult]

class Problem(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    difficulty: str
    tags: List[str]

class UserProgress(BaseModel):
    user_id: str
    problem_id: str
    solved: bool
    best_score: int
    attempts: int
