from fastapi import APIRouter
from app.services.supabase import SupabaseClient

router = APIRouter(prefix="/problems", tags=["Problems"])
sb = SupabaseClient()

@router.get("/")
async def list_problems():
    return await sb.get("problems")

@router.get("/{problem_id}")
async def get_problem(problem_id: str):
    problems = await sb.get("problems", {"id": f"eq.{problem_id}"})
    testcases = await sb.get(
        "testcases",
        {"problem_id": f"eq.{problem_id}", "is_sample": "eq.true"},
    )

    return {
        "problem": problems[0] if problems else None,
        "sample_testcases": testcases,
    }
