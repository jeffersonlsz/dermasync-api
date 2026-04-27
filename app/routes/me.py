# app/routes/me.py
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

router = APIRouter(prefix="/me", tags=["me"])

@router.get("/profile")
def profile_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
