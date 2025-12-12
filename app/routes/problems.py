from fastapi import APIRouter, HTTPException
from app.services.supabase import SupabaseClient

router = APIRouter(prefix="/problems", tags=["Problems"])
sb_admin = SupabaseClient(admin=True)

@router.get("/")
async def list_problems(user_id: str = None):
    """
    List all problems with optional user progress
    If user_id is provided, include solved status
    """
    try:
        # Get all problems
        problems = await sb_admin.get(
            "problems",
            {"select": "id,title,slug,difficulty,tags"}
        )
        
        if not user_id:
            return {"problems": problems}
        
        # Get user progress for this user
        progress = await sb_admin.get(
            "user_progress",
            {"user_id": f"eq.{user_id}", "select": "problem_id,solved,best_score,attempts"}
        )
        
        # Create a map of problem_id -> progress
        progress_map = {p["problem_id"]: p for p in progress}
        
        # Enrich problems with progress data
        for problem in problems:
            prog = progress_map.get(problem["id"])
            if prog:
                problem["solved"] = prog["solved"]
                problem["best_score"] = prog["best_score"]
                problem["attempts"] = prog["attempts"]
            else:
                problem["solved"] = False
                problem["best_score"] = 0
                problem["attempts"] = 0
        
        return {"problems": problems}
        
    except Exception as e:
        print(f"Error fetching problems: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{problem_id}")
async def get_problem(problem_id: str):
    """Get a single problem by ID with sample test cases"""
    try:
        problems = await sb_admin.get("problems", {"id": f"eq.{problem_id}"})
        if not problems:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        return {"problem": problems[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching problem: {e}")
        raise HTTPException(status_code=500, detail=str(e))
