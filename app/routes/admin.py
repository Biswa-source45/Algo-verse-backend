from fastapi import APIRouter, Depends, HTTPException
from app.routes.deps import require_admin, get_current_user
from app.services.supabase import SupabaseClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/admin", tags=["Admin"])
sb_admin = SupabaseClient(admin=True)


class ProblemCreate(BaseModel):
    title: str
    slug: str
    description: str
    difficulty: str
    tags: List[str] = []


class TestCaseCreate(BaseModel):
    problem_id: str
    input: str
    expected_output: str
    is_sample: bool = False
    points: int = 10


@router.get("/stats")
async def get_stats(admin=Depends(require_admin)):
    """Get dashboard statistics"""
    try:
        # Get counts
        users = await sb_admin.get("profiles", {"role": "eq.coder", "select": "id"})
        problems = await sb_admin.get("problems", {"select": "id"})
        submissions = await sb_admin.get("submissions", {"select": "id,passed"})
        
        successful = len([s for s in submissions if s.get("passed")])
        
        return {
            "total_users": len(users),
            "total_problems": len(problems),
            "total_submissions": len(submissions),
            "successful_submissions": successful
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/users")
async def get_all_users(admin=Depends(require_admin)):
    """Get all users with their stats"""
    try:
        # Get all coders
        users = await sb_admin.get(
            "profiles", 
            {"role": "eq.coder", "select": "id,username,display_name,created_at"}
        )
        
        # Get progress for each user
        for user in users:
            progress = await sb_admin.get(
                "user_progress",
                {"user_id": f"eq.{user['id']}", "select": "*"}
            )
            user["problems_solved"] = len([p for p in progress if p.get("solved")])
            user["total_attempts"] = sum(p.get("attempts", 0) for p in progress)
        
        return {"users": users}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/problems")
async def create_problem(problem: ProblemCreate, admin=Depends(require_admin)):
    """Create a new problem"""
    try:
        problem_id = str(uuid.uuid4())
        
        problem_data = {
            "id": problem_id,
            "title": problem.title,
            "slug": problem.slug,
            "description": problem.description,
            "difficulty": problem.difficulty,
            "tags": problem.tags,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        created = await sb_admin.post("problems", problem_data)
        return {"problem": created, "message": "Problem created successfully"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/problems/{problem_id}")
async def update_problem(problem_id: str, problem: ProblemCreate, admin=Depends(require_admin)):
    """Update an existing problem"""
    try:
        updates = {
            "title": problem.title,
            "slug": problem.slug,
            "description": problem.description,
            "difficulty": problem.difficulty,
            "tags": problem.tags
        }
        
        updated = await sb_admin.patch("problems", {"id": f"eq.{problem_id}"}, updates)
        return {"problem": updated, "message": "Problem updated successfully"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/problems/{problem_id}")
async def delete_problem(problem_id: str, admin=Depends(require_admin)):
    """Delete a problem"""
    try:
        await sb_admin.delete("problems", {"id": f"eq.{problem_id}"})
        return {"message": "Problem deleted successfully"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/testcases")
async def add_testcase(testcase: TestCaseCreate, admin=Depends(require_admin)):
    """Add a test case to a problem"""
    try:
        testcase_data = {
            "id": str(uuid.uuid4()),
            "problem_id": testcase.problem_id,
            "input": testcase.input,
            "expected_output": testcase.expected_output,
            "is_sample": testcase.is_sample,
            "points": testcase.points,
        }
        
        created = await sb_admin.post("testcases", testcase_data)
        return {"testcase": created, "message": "Test case added successfully"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/problems/{problem_id}/testcases")
async def get_problem_testcases(problem_id: str, admin=Depends(require_admin)):
    """Get all test cases for a problem (including hidden ones)"""
    try:
        testcases = await sb_admin.get("testcases", {"problem_id": f"eq.{problem_id}"})
        return {"testcases": testcases}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
