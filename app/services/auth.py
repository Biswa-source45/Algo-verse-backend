import httpx
from fastapi import HTTPException
from app.config import settings

async def get_user_from_token(token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers=headers,
        )

    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    return res.json()
