from fastapi import APIRouter, Depends, HTTPException
from app.routes.deps import get_current_user
from app.services.supabase import SupabaseClient
from app.services.piston import run_code
from app.services.evaluator import is_correct
from app.schemas import ExecutePayload
from datetime import datetime, timezone
import time
import uuid
from typing import List, Dict
import traceback

router = APIRouter(prefix="/submit", tags=["Submit"])
sb_admin = SupabaseClient(admin=True)

@router.post("/{problem_id}")
async def submit(problem_id: str, payload: ExecutePayload, user_id=Depends(get_current_user)):
    """
    Submit a solution for a problem
    Runs code against all test cases and stores results
    """
    submission_id = None
    
    try:
        print(f"\n{'='*60}")
        print(f"SUBMISSION STARTED")
        print(f"User: {user_id}, Problem: {problem_id}, Language: {payload.language}")
        print(f"{'='*60}\n")
        
        # 1. Validate Language
        langs = await sb_admin.get("languages", {"slug": f"eq.{payload.language}"})
        if not langs:
            raise HTTPException(status_code=400, detail="Invalid language selected")
        
        lang_config = langs[0]
        executor_lang = lang_config["executor_key"]
        print(f"✓ Language validated: {executor_lang}")

        # 2. Get All Testcases
        testcases = await sb_admin.get(
            "testcases",
            {"problem_id": f"eq.{problem_id}", "select": "*"}
        )

        if not testcases:
            raise HTTPException(status_code=404, detail="No test cases found")
        
        print(f"✓ Found {len(testcases)} test cases")

        # 3. Execute code against each testcase
        submission_results: List[Dict] = []
        passed_count = 0
        total_score = 0
        all_passed = True
        main_output = ""
        
        for idx, tc in enumerate(testcases):
            print(f"\nRunning test case {idx + 1}/{len(testcases)}...")
            start_time = time.time()
            
            output = await run_code(executor_lang, payload.code, tc["input"])
            duration_ms = int((time.time() - start_time) * 1000)

            is_error = output.startswith("Error:") or output.startswith("Compilation Error:") or output.startswith("Runtime Error:")
            
            if is_error:
                passed = False
                all_passed = False
                if not main_output:
                    main_output = output
                print(f"  ✗ Failed (error)")
            else:
                passed = is_correct(tc["expected_output"], output)
                if passed:
                    passed_count += 1
                    total_score += tc.get("points", 0)
                    if not main_output:
                        main_output = output
                    print(f"  ✓ Passed ({duration_ms}ms)")
                else:
                    all_passed = False
                    if not main_output:
                        main_output = output
                    print(f"  ✗ Wrong answer ({duration_ms}ms)")

            submission_results.append({
                "testcase_id": str(tc["id"]),
                "passed": passed,
                "actual_output": output[:1000],
                "runtime_ms": duration_ms
            })

        print(f"\n{'='*60}")
        print(f"EXECUTION COMPLETE: {passed_count}/{len(testcases)} passed")
        print(f"Total Score: {total_score}")
        print(f"{'='*60}\n")

        # 4. Create submission record with EXPLICIT UUID
        submission_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        submission_data = {
            "id": submission_id,
            "user_id": str(user_id),
            "problem_id": str(problem_id),
            "language_slug": payload.language,
            "code": payload.code,
            "passed": all_passed,
            "score": total_score,
            "output": main_output[:500] if main_output else "",
            "created_at": current_time,
        }
        
        print(f"Inserting submission with ID: {submission_id}")
        
        try:
            inserted = await sb_admin.post("submissions", submission_data)
            print(f"✓ Submission created successfully")
        except Exception as submit_error:
            print(f"✗ Submission insert failed: {submit_error}")
            # Generate new ID and retry
            submission_id = str(uuid.uuid4())
            submission_data["id"] = submission_id
            submission_data["created_at"] = datetime.now(timezone.utc).isoformat()
            print(f"Retrying with new ID: {submission_id}")
            inserted = await sb_admin.post("submissions", submission_data)
            print(f"✓ Submission created on retry")

        # 5. Store test case results
        if submission_results:
            print(f"Inserting {len(submission_results)} test results...")
            results_to_insert = []
            for res in submission_results:
                results_to_insert.append({
                    "id": str(uuid.uuid4()),
                    "submission_id": submission_id,
                    "testcase_id": res["testcase_id"],
                    "passed": res["passed"],
                    "actual_output": res["actual_output"],
                    "runtime_ms": res["runtime_ms"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            
            try:
                await sb_admin.post("submission_results", results_to_insert)
                print(f"✓ Test results saved")
            except Exception as e:
                print(f"Warning: Failed to store results: {e}")

        # 6. Update user progress
        print(f"Updating user progress...")
        try:
            existing = await sb_admin.get(
                "user_progress",
                {"user_id": f"eq.{user_id}", "problem_id": f"eq.{problem_id}"}
            )

            if existing and len(existing) > 0:
                curr = existing[0]
                updates = {
                    "attempts": curr.get("attempts", 0) + 1,
                    "last_submission_at": datetime.now(timezone.utc).isoformat(),
                }
                
                if all_passed and not curr.get("solved", False):
                    updates["solved"] = True
                
                if total_score > curr.get("best_score", 0):
                    updates["best_score"] = total_score
                    
                await sb_admin.patch("user_progress", {"id": f"eq.{curr['id']}"}, updates)
                print(f"✓ Progress updated")
            else:
                new_progress = {
                    "id": str(uuid.uuid4()),
                    "user_id": str(user_id),
                    "problem_id": str(problem_id),
                    "solved": all_passed,
                    "best_score": total_score,
                    "attempts": 1,
                    "last_submission_at": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                await sb_admin.post("user_progress", new_progress)
                print(f"✓ Progress created")
        except Exception as e:
            print(f"Warning: Progress update failed: {e}")

        print(f"\n{'='*60}")
        print(f"SUBMISSION SUCCESSFUL")
        print(f"{'='*60}\n")

        # 7. Return results
        return {
            "passed": all_passed,
            "score": total_score,
            "submission_id": submission_id,
            "total_tests": len(testcases),
            "passed_tests": passed_count,
            "results": submission_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        print(f"\n{'='*60}")
        print(f"SUBMISSION FAILED")
        print(f"Error: {error_detail}")
        print(f"{'='*60}\n")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Submission failed: {error_detail}")
