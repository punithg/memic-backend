"""User controller for profile management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dtos.auth_dto import UserResponse
from app.dtos.user_dto import UserUpdate
from app.models import User
from app.services.user_service import UserService
from app.core.auth import get_current_user


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile information.
    
    Requires authentication.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    - **name**: Optional new name
    - **email**: Optional new email (must be unique)
    
    Requires authentication.
    """
    user_service = UserService(db)
    updated_user = user_service.update_user(current_user, update_data)
    return UserResponse.model_validate(updated_user)

