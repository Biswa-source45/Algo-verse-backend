from fastapi import Header, HTTPException
from app.services.auth import get_user_from_token
from app.services.supabase import SupabaseClient

sb_admin = SupabaseClient(admin=True)

async def get_current_user(authorization: str = Header(...)):
    """Get current user ID from token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid auth header")

    token = authorization.replace("Bearer ", "")
    user = await get_user_from_token(token)
    return user["id"]


async def require_admin(authorization: str = Header(...)):
    """Require admin role - returns user profile if admin"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid auth header")

    token = authorization.replace("Bearer ", "")
    user = await get_user_from_token(token)
    user_id = user["id"]
    
    # Get user profile to check role
    profiles = await sb_admin.get("profiles", {"id": f"eq.{user_id}"})
    
    if not profiles or len(profiles) == 0:
        raise HTTPException(403, "Profile not found")
    
    profile = profiles[0]
    
    if profile.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    return profile
