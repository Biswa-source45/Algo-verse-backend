from fastapi import APIRouter, Depends
from app.routes.deps import get_current_user
from app.services.supabase import SupabaseClient
from app.services.piston import run_code
from app.services.evaluator import is_correct
from datetime import datetime

router = APIRouter(prefix="/submit", tags=["Submit"])
sb_admin = SupabaseClient(admin=True)

@router.post("/{problem_id}")
async def submit(problem_id: str, payload: dict, user_id=Depends(get_current_user)):

    testcases = await sb_admin.get(
        "testcases",
        {"problem_id": f"eq.{problem_id}"}
    )

    passed_all = True
    score = 0

    for tc in testcases:
        output = await run_code(payload["language"], payload["code"], tc["input"])

        if is_correct(tc["expected_output"], output):
            score += tc["points"]
        else:
            passed_all = False

    await sb_admin.post("submissions", {
        "user_id": user_id,
        "problem_id": problem_id,
        "language_slug": payload["language"],
        "code": payload["code"],
        "passed": passed_all,
        "score": score,
        "created_at": datetime.utcnow().isoformat(),
    })

    return {
        "passed": passed_all,
        "score": score,
    }
