from fastapi import Header, HTTPException
from app.services.auth import get_user_from_token

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid auth header")

    token = authorization.replace("Bearer ", "")
    user = await get_user_from_token(token)
    return user["id"]
