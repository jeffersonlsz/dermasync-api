# app/routes/me.py
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.users.models import User as DBUser

router = APIRouter(prefix="/me", tags=["me"])

@router.get("/profile")
def profile_me(current_user: DBUser = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat()
    }
