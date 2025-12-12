from fastapi import APIRouter, HTTPException
from app.services.supabase import SupabaseClient
from app.services.piston import run_code
from app.services.evaluator import is_correct
from app.schemas import ExecutePayload

router = APIRouter(prefix="/run", tags=["Run"])
sb_admin = SupabaseClient(admin=True)

@router.post("/{problem_id}")
async def run_sample(problem_id: str, payload: ExecutePayload):
    """
    Run code against SAMPLE test cases only (for testing before submission)
    This is a public endpoint - no authentication required
    """
    try:
        # 1. Validate Language
        langs = await sb_admin.get("languages", {"slug": f"eq.{payload.language}"})
        if not langs:
            raise HTTPException(status_code=400, detail="Invalid language selected")
        
        executor_lang = langs[0]["executor_key"]

        # 2. Get ONLY Sample Testcases (is_sample = true)
        testcases = await sb_admin.get(
            "testcases",
            {"problem_id": f"eq.{problem_id}", "is_sample": "eq.true"}
        )

        if not testcases:
            raise HTTPException(status_code=404, detail="No sample test cases found")

        # 3. Run against the first sample testcase
        tc = testcases[0]
        output = await run_code(executor_lang, payload.code, tc["input"])
        
        # Check if it's an error
        is_error = output.startswith("Error:") or output.startswith("Compilation Error:") or output.startswith("Runtime Error:")
        
        return {
            "input": tc["input"],
            "expected": tc["expected_output"],
            "output": output,
            "passed": is_correct(tc["expected_output"], output) if not is_error else False,
            "is_error": is_error
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Run error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
