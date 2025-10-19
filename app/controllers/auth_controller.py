"""Authentication controller for signup and login endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dtos.auth_dto import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.services.user_service import UserService
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new user account.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **name**: User's full name
    """
    user_service = UserService(db)
    user = user_service.create_user(signup_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password to get JWT access token.
    
    - **email**: User email address
    - **password**: User password
    """
    user_service = UserService(db)
    
    # Authenticate user
    user = user_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token, expires_in = AuthService.create_access_token(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in
    )

