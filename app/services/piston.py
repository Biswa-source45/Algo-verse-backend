import httpx
from typing import Dict, Any

PISTON_URL = "https://emkc.org/api/v2/piston/execute"

async def run_code(language: str, code: str, stdin: str, version: str = "*") -> str:
    """
    Execute code using Piston API
    Returns the output (stdout) or error message
    """
    payload = {
        "language": language,
        "version": version,
        "files": [
            {
                "name": f"main.{get_file_extension(language)}",
                "content": code
            }
        ],
        "stdin": stdin,
        "compile_timeout": 10000,
        "run_timeout": 3000,
        "compile_memory_limit": -1,
        "run_memory_limit": -1
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(PISTON_URL, json=payload)
            res.raise_for_status()
            
            data = res.json()
            
            # Check if there's a compile stage (for compiled languages)
            if "compile" in data and data["compile"].get("code") != 0:
                compile_output = data["compile"].get("stderr") or data["compile"].get("stdout") or "Compilation failed"
                return f"Compilation Error:\n{compile_output}"
            
            # Get run stage output
            run_stage = data.get("run", {})
            
            # Check for runtime errors
            if run_stage.get("code") != 0:
                error_output = run_stage.get("stderr", "")
                if error_output:
                    return f"Runtime Error:\n{error_output}"
            
            # Return stdout (the actual output)
            output = run_stage.get("stdout", "").strip()
            
            # If no stdout but there's stderr, return that
            if not output:
                stderr = run_stage.get("stderr", "").strip()
                if stderr:
                    return stderr
            
            return output
            
    except httpx.TimeoutException:
        return "Error: Code execution timed out (max 30s)"
    except httpx.HTTPError as e:
        return f"Error: Failed to execute code - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def get_file_extension(language: str) -> str:
    """Get appropriate file extension for language"""
    extensions = {
        "python": "py",
        "javascript": "js",
        "cpp": "cpp",
        "java": "java",
        "c": "c",
        "rust": "rs",
        "go": "go",
    }
    return extensions.get(language, "txt")
