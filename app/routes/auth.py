from fastapi import APIRouter, Depends, HTTPException, Header
from app.routes.deps import get_current_user
from app.services.supabase import SupabaseClient
from app.services.auth import get_user_from_token
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])
sb_admin = SupabaseClient(admin=True)

@router.get("/me")
async def get_my_profile(authorization: str = Header(...)):
    """
    Get current user profile from database
    Creates profile if it doesn't exist
    Returns profile with email from Supabase Auth
    """
    try:
        # Validate auth header
        if not authorization.startswith("Bearer "):
            raise HTTPException(401, "Invalid auth header")
        
        token = authorization.replace("Bearer ", "")
        
        # Get user from Supabase Auth
        auth_user = await get_user_from_token(token)
        user_id = auth_user["id"]
        user_email = auth_user.get("email", "")
        
        print(f"🔍 Fetching profile for: {user_email} (ID: {user_id})")
        
        # Check if profile exists in database
        profiles = await sb_admin.get("profiles", {"id": f"eq.{user_id}"})
        
        if not profiles or len(profiles) == 0:
            print(f"📝 Profile not found for {user_email}, creating new profile...")
            
            # Extract username from email (part before @)
            username = user_email.split('@')[0] if user_email else f"user{user_id[:8]}"
            
            # Determine role based on email
            role = "admin" if user_email == "biswapvt506@gmail.com" else "coder"
            
            # Create new profile
            new_profile = {
                "id": str(user_id),
                "username": username,
                "display_name": username.capitalize(),  # Capitalize first letter
                "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_id}",
                "bio": None,
                "role": role,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await sb_admin.post("profiles", new_profile)
            print(f"✅ Profile created: {username} ({role})")
            
            # Return profile with email
            new_profile["email"] = user_email
            return new_profile
        
        # Profile exists, return it with email from auth
        profile = profiles[0]
        profile["email"] = user_email
        
        print(f"✅ Profile found: {profile['username']} ({profile.get('role', 'coder')})")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in /auth/me: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")
