import httpx

PISTON_URL = "https://emkc.org/api/v2/piston/execute"

async def run_code(language: str, code: str, stdin: str):
    payload = {
        "language": language,
        "source": code,
        "stdin": stdin,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(PISTON_URL, json=payload)

    data = res.json()
    return data["run"]["output"]
